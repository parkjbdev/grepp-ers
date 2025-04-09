import logging
import sys
import unittest
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from asyncpg import ExclusionViolationError, Range

from app.dependencies.config import database
from app.repositories.slot.dbimpl import SlotRepositoryImpl
from app.repositories.slot.exceptions import NoSuchSlotException, SlotTimeRangeOverlapped
from app.models.slot_model import Slot


class TestSlotRepository(unittest.IsolatedAsyncioTestCase):
    """슬롯 레포지토리 구현체에 대한 테스트 클래스"""

    # 테스트 클래스 로거 설정
    logger = logging.getLogger('TestSlotRepository')

    async def asyncSetUp(self):
        """각 테스트 실행 전 데이터베이스 연결 및 테스트 데이터 초기화"""
        self.logger.info("테스트 환경 설정 시작")
        load_dotenv()
        self.logger.info("데이터베이스 연결 중...")
        await database.connect()
        self.pool = database.get_pool()
        self.logger.info("SlotRepositoryImpl 인스턴스 생성 중...")
        self.repo = SlotRepositoryImpl(self.pool)

        # 테스트 데이터 정리
        self.logger.info("이전 테스트 데이터 정리 중...")
        async with self.pool.acquire() as conn:
            await conn.execute("DELETE FROM slots WHERE id < 1000")  # 테스트용 슬롯 ID는 1000 미만으로 가정
        self.logger.info("테스트 환경 설정 완료")

    async def asyncTearDown(self):
        """각 테스트 실행 후 테스트 데이터 정리 및 데이터베이스 연결 해제"""
        self.logger.info("테스트 정리 시작")
        # 테스트 데이터 정리
        self.logger.info("테스트 데이터 삭제 중...")
        async with self.pool.acquire() as conn:
            await conn.execute("DELETE FROM slots WHERE id < 1000")
        self.logger.info("데이터베이스 연결 해제 중...")
        await database.disconnect()
        self.logger.info("테스트 정리 완료")

    async def test_find_slots_with_time_range(self):
        """시간 범위로 슬롯 조회가 성공적으로 이루어지는지 테스트"""
        # given
        start_time = datetime.now(timezone.utc)
        end_time = start_time + timedelta(hours=1)
        slot = Slot.create_with_time_range(start_time, end_time)
        await self.repo.insert(slot)

        # when
        slots = await self.repo.find(start_time, end_time)

        # then
        self.assertEqual(len(slots), 1, "조회된 슬롯이 1개여야 합니다.")
        self.assertEqual(slots[0]["time_range"].lower, start_time, "시작 시간이 일치해야 합니다.")
        self.assertEqual(slots[0]["time_range"].upper, end_time, "종료 시간이 일치해야 합니다.")

    async def test_find_slot_by_id_success(self):
        """ID로 슬롯 조회가 성공적으로 이루어지는지 테스트"""
        # given
        start_time = datetime.now(timezone.utc)
        end_time = start_time + timedelta(hours=1)
        slot = Slot.create_with_time_range(start_time, end_time)
        result = await self.repo.insert(slot)
        slot_id = result["id"]

        # when
        found_slot = await self.repo.find_by_id(slot_id)

        # then
        self.assertIsNotNone(found_slot, "조회된 슬롯이 None이면 안 됩니다.")
        self.assertEqual(found_slot["id"], slot_id, "조회된 슬롯의 ID가 일치해야 합니다.")
        self.assertEqual(found_slot["time_range"].lower, start_time, "시작 시간이 일치해야 합니다.")
        self.assertEqual(found_slot["time_range"].upper, end_time, "종료 시간이 일치해야 합니다.")

    async def test_find_slot_by_id_not_found(self):
        """존재하지 않는 슬롯 ID로 조회 시 예외가 발생하는지 테스트"""
        # given
        non_existent_id = 999999

        # when & then
        with self.assertRaises(NoSuchSlotException):
            await self.repo.find_by_id(non_existent_id)

    async def test_insert_slot_success(self):
        """슬롯 생성이 성공적으로 이루어지는지 테스트"""
        # given
        start_time = datetime.now(timezone.utc)
        end_time = start_time + timedelta(hours=1)
        slot = Slot.create_with_time_range(start_time, end_time)

        # when
        result = await self.repo.insert(slot)

        # then
        self.assertIsNotNone(result, "삽입 결과가 None이면 안 됩니다.")
        self.assertIn("id", result, "삽입 결과에 'id' 필드가 포함되어야 합니다.")

        # 검증을 위해 데이터 조회
        async with self.pool.acquire() as conn:
            slot_data = await conn.fetchrow("SELECT * FROM slots WHERE id = $1", result["id"])
        self.assertIsNotNone(slot_data, "생성된 슬롯이 데이터베이스에 존재해야 합니다.")
        self.assertEqual(slot_data["time_range"].lower, start_time, "시작 시간이 일치해야 합니다.")
        self.assertEqual(slot_data["time_range"].upper, end_time, "종료 시간이 일치해야 합니다.")

    async def test_insert_slot_overlap(self):
        """중복된 시간대의 슬롯 생성 시 예외가 발생하는지 테스트"""
        # given
        start_time = datetime.now()
        end_time = start_time + timedelta(hours=1)
        slot1 = Slot.create_with_time_range(start_time, end_time)
        slot2 = Slot.create_with_time_range(start_time, end_time)

        # 첫 번째 슬롯 생성
        await self.repo.insert(slot1)

        # when & then - 두 번째 슬롯 생성 시 예외 발생해야 함
        with self.assertRaises(SlotTimeRangeOverlapped):
            await self.repo.insert(slot2)

    async def test_modify_slot_success(self):
        """슬롯 수정이 성공적으로 이루어지는지 테스트"""
        # given
        start_time = datetime.now(timezone.utc)
        end_time = start_time + timedelta(hours=1)
        slot = Slot.create_with_time_range(start_time, end_time)
        result = await self.repo.insert(slot)
        slot_id = result["id"]

        # 수정할 시간 범위
        new_start_time = start_time + timedelta(hours=2)
        new_end_time = end_time + timedelta(hours=2)
        updated_slot = Slot.create_with_time_range(new_start_time, new_end_time, id=slot_id)

        # when
        result = await self.repo.modify(updated_slot)

        # then
        self.assertIsNotNone(result, "수정 결과가 None이면 안 됩니다.")
        self.assertEqual(result["id"], slot_id, "수정된 슬롯의 ID가 일치해야 합니다.")

        # 검증을 위해 데이터 조회
        async with self.pool.acquire() as conn:
            slot_data = await conn.fetchrow("SELECT * FROM slots WHERE id = $1", slot_id)
        self.assertEqual(slot_data["time_range"].lower, new_start_time, "수정된 시작 시간이 일치해야 합니다.")
        self.assertEqual(slot_data["time_range"].upper, new_end_time, "수정된 종료 시간이 일치해야 합니다.")

    async def test_modify_slot_not_found(self):
        """존재하지 않는 슬롯 수정 시 예외가 발생하는지 테스트"""
        # given
        non_existent_id = 999999
        start_time = datetime.now()
        end_time = start_time + timedelta(hours=1)
        slot = Slot.create_with_time_range(start_time, end_time, id=non_existent_id)

        # when & then
        with self.assertRaises(NoSuchSlotException):
            await self.repo.modify(slot)

    async def test_delete_slot_success(self):
        """슬롯 삭제가 성공적으로 이루어지는지 테스트"""
        # given
        start_time = datetime.now()
        end_time = start_time + timedelta(hours=1)
        slot = Slot.create_with_time_range(start_time, end_time)
        result = await self.repo.insert(slot)
        slot_id = result["id"]

        # when
        result = await self.repo.delete(slot_id)

        # then
        self.assertIsNotNone(result, "삭제 결과가 None이면 안 됩니다.")
        self.assertEqual(result["id"], slot_id, "삭제된 슬롯의 ID가 일치해야 합니다.")

        # 검증을 위해 데이터 조회
        async with self.pool.acquire() as conn:
            slot_data = await conn.fetchrow("SELECT * FROM slots WHERE id = $1", slot_id)
        self.assertIsNone(slot_data, "삭제된 슬롯은 조회되지 않아야 합니다.")

    async def test_delete_slot_not_found(self):
        """존재하지 않는 슬롯 삭제 시 예외가 발생하는지 테스트"""
        # given
        non_existent_id = 999999

        # when & then
        with self.assertRaises(NoSuchSlotException):
            await self.repo.delete(non_existent_id)


if __name__ == '__main__':
    # 로그 설정
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        stream=sys.stdout
    )

    # TestRunner 설정
    runner = unittest.TextTestRunner(verbosity=3)

    # 테스트 실행
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSlotRepository)
    runner.run(suite)
