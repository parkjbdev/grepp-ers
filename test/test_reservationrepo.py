import logging
import sys
import unittest
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

from app.dependencies.config import database
from app.repositories.reservation.dbimpl_transaction import ReservationRepositoryTransactionImpl
from app.repositories.reservation.exceptions import (
    DaysNotLeftEnoughException, NoSuchReservationException,
    ReservationAlreadyConfirmedException, UserMismatchException
)
from app.models.reservation_model import Reservation, ReservationDto

class TestReservationRepository(unittest.IsolatedAsyncioTestCase):
    """예약 레포지토리 구현체에 대한 테스트 클래스"""

    # 테스트 클래스 로거 설정
    logger = logging.getLogger('TestReservationRepository')

    async def asyncSetUp(self):
        """각 테스트 실행 전 데이터베이스 연결 및 테스트 데이터 초기화"""
        self.logger.info("테스트 환경 설정 시작")
        load_dotenv()
        self.logger.info("데이터베이스 연결 중...")
        await database.connect()
        self.pool = database.get_pool()
        self.logger.info("ReservationRepositoryImpl 인스턴스 생성 중...")
        self.repo = ReservationRepositoryTransactionImpl(self.pool)

        # 테스트 데이터 정리
        self.logger.info("이전 테스트 데이터 정리 중...")
        async with self.pool.acquire() as conn:
            await conn.execute("DELETE FROM reservations WHERE id < 1000")  # 테스트용 예약 ID는 1000 미만으로 가정
            await conn.execute("DELETE FROM slots WHERE id < 1000")  # 테스트용 슬롯 ID는 1000 미만으로 가정
            await conn.execute("DELETE FROM users WHERE id < 1000")  # 테스트용 사용자 ID는 1000 미만으로 가정
        self.logger.info("테스트 환경 설정 완료")

    async def asyncTearDown(self):
        """각 테스트 실행 후 테스트 데이터 정리 및 데이터베이스 연결 해제"""
        self.logger.info("테스트 정리 시작")
        # 테스트 데이터 정리
        self.logger.info("테스트 데이터 삭제 중...")
        async with self.pool.acquire() as conn:
            await conn.execute("DELETE FROM reservations WHERE id < 1000")
            await conn.execute("DELETE FROM slots WHERE id < 1000")
            await conn.execute("DELETE FROM users WHERE id < 1000")
        self.logger.info("데이터베이스 연결 해제 중...")
        await database.disconnect()
        self.logger.info("테스트 정리 완료")

    async def test_insert_reservation_success(self):
        """예약 생성이 성공적으로 이루어지는지 테스트"""
        # given
        # 테스트용 사용자 생성
        async with self.pool.acquire() as conn:
            user = await conn.fetchrow(
                "INSERT INTO users(username, password) VALUES($1, $2) RETURNING id",
                "test_user", "test_password"
            )
            user_id = user["id"]

            # 테스트용 슬롯 생성
            start_time = datetime.now()
            end_time = start_time + timedelta(hours=1)
            slot = await conn.fetchrow(
                "INSERT INTO slots(time_range) VALUES($1) RETURNING id",
                (start_time, end_time)
            )
            slot_id = slot["id"]

        reservation = Reservation(
            id=None,
            user_id=user_id,
            slot_id=slot_id,
            amount=1,
            confirmed=False,
            time_range=(start_time, end_time)
        )

        # when
        result = await self.repo.insert(reservation)

        # then
        self.assertIsNotNone(result, "삽입 결과가 None이면 안 됩니다.")
        self.assertIn("id", result, "삽입 결과에 'id' 필드가 포함되어야 합니다.")

        # 검증을 위해 데이터 조회
        async with self.pool.acquire() as conn:
            reservation_data = await conn.fetchrow(
                "SELECT * FROM reservations WHERE id = $1",
                result["id"]
            )
        self.assertIsNotNone(reservation_data, "생성된 예약이 데이터베이스에 존재해야 합니다.")
        self.assertEqual(reservation_data["user_id"], user_id, "사용자 ID가 일치해야 합니다.")
        self.assertEqual(reservation_data["slot_id"], slot_id, "슬롯 ID가 일치해야 합니다.")
        self.assertEqual(reservation_data["amount"], 1, "예약 수량이 일치해야 합니다.")
        self.assertFalse(reservation_data["confirmed"], "예약은 미확정 상태여야 합니다.")

    async def test_insert_reservation_if_days_left_success(self):
        """남은 일수가 충분할 때 예약 생성이 성공적으로 이루어지는지 테스트"""
        # given
        # 테스트용 사용자 생성
        async with self.pool.acquire() as conn:
            user = await conn.fetchrow(
                "INSERT INTO users(username, password) VALUES($1, $2) RETURNING id",
                "test_user", "test_password"
            )
            user_id = user["id"]

            # 테스트용 슬롯 생성
            start_time = datetime.now(timezone.utc) + timedelta(days=7, seconds=1)  # 7일 후
            # 1 second is for delay between server and db
            end_time = start_time + timedelta(hours=1)
            slot = await conn.fetchrow(
                "INSERT INTO slots(time_range) VALUES($1) RETURNING id",
                (start_time, end_time)
            )
            slot_id = slot["id"]

        reservation = Reservation(
            id=None,
            user_id=user_id,
            slot_id=slot_id,
            amount=1,
            confirmed=False,
        )

        # when
        result = await self.repo.insert_if_days_left(reservation, days_left=7)

        # then
        self.assertIsNotNone(result, "삽입 결과가 None이면 안 됩니다.")
        self.assertIn("id", result, "삽입 결과에 'id' 필드가 포함되어야 합니다.")

    async def test_insert_reservation_if_days_left_failure(self):
        """남은 일수가 부족할 때 예약 생성이 실패하는지 테스트"""
        # given
        # 테스트용 사용자 생성
        async with self.pool.acquire() as conn:
            user = await conn.fetchrow(
                "INSERT INTO users(username, password) VALUES($1, $2) RETURNING id",
                "test_user", "test_password"
            )
            user_id = user["id"]

            # 테스트용 슬롯 생성
            start_time = datetime.now() + timedelta(days=6)  # 6일 후
            end_time = start_time + timedelta(hours=1)
            slot = await conn.fetchrow(
                "INSERT INTO slots(time_range) VALUES($1) RETURNING id",
                (start_time, end_time)
            )
            slot_id = slot["id"]

        reservation = Reservation(
            id=None,
            user_id=user_id,
            slot_id=slot_id,
            amount=1,
            confirmed=False,
        )

        # when & then
        with self.assertRaises(DaysNotLeftEnoughException):
            await self.repo.insert_if_days_left(reservation, days_left=7)

    async def test_confirm_reservation_success(self):
        """예약 확정이 성공적으로 이루어지는지 테스트"""
        # given
        # 테스트용 사용자 생성
        async with self.pool.acquire() as conn:
            user = await conn.fetchrow(
                "INSERT INTO users(username, password) VALUES($1, $2) RETURNING id",
                "test_user", "test_password"
            )
            user_id = user["id"]

            # 테스트용 슬롯 생성
            start_time = datetime.now()
            end_time = start_time + timedelta(hours=1)
            slot = await conn.fetchrow(
                "INSERT INTO slots(time_range) VALUES($1) RETURNING id",
                (start_time, end_time)
            )
            slot_id = slot["id"]

            # 테스트용 예약 생성
            reservation = await conn.fetchrow(
                "INSERT INTO reservations(user_id, slot_id, amount, confirmed) VALUES($1, $2, $3, $4) RETURNING id",
                user_id, slot_id, 1, False
            )
            reservation_id = reservation["id"]

        # when
        result = await self.repo.confirm_by_id(reservation_id)

        # then
        self.assertIsNotNone(result, "확정 결과가 None이면 안 됩니다.")
        self.assertEqual(result["id"], reservation_id, "확정된 예약의 ID가 일치해야 합니다.")

        # 검증을 위해 데이터 조회
        async with self.pool.acquire() as conn:
            reservation_data = await conn.fetchrow(
                "SELECT * FROM reservations WHERE id = $1",
                reservation_id
            )
        self.assertTrue(reservation_data["confirmed"], "예약이 확정 상태여야 합니다.")

    async def test_confirm_reservation_not_found(self):
        """존재하지 않는 예약 확정 시 예외가 발생하는지 테스트"""
        # given
        non_existent_id = 999999

        # when & then
        with self.assertRaises(NoSuchReservationException):
            await self.repo.confirm_by_id(non_existent_id)

    async def test_modify_from_admin_success(self):
        """관리자가 예약 수정이 성공적으로 이루어지는지 테스트"""
        # given
        # 테스트용 사용자 생성
        async with self.pool.acquire() as conn:
            user = await conn.fetchrow(
                "INSERT INTO users(username, password) VALUES($1, $2) RETURNING id",
                "test_user", "test_password"
            )
            user_id = user["id"]

            # 테스트용 슬롯 생성
            start_time = datetime.now()
            end_time = start_time + timedelta(hours=1)
            slot = await conn.fetchrow(
                "INSERT INTO slots(time_range) VALUES($1) RETURNING id",
                (start_time, end_time)
            )
            slot_id = slot["id"]

            # 테스트용 예약 생성
            reservation = await conn.fetchrow(
                "INSERT INTO reservations(user_id, slot_id, amount, confirmed) VALUES($1, $2, $3, $4) RETURNING id",
                user_id, slot_id, 1, False
            )
            reservation_id = reservation["id"]

        # 수정할 예약 정보
        reservation_dto = ReservationDto(
            slot_id=slot_id,
            amount=2,
            time_range=(start_time, end_time)
        )

        # when
        result = await self.repo.modify_from_admin(reservation_id, reservation_dto)

        # then
        self.assertIsNotNone(result, "수정 결과가 None이면 안 됩니다.")
        self.assertEqual(result["id"], reservation_id, "수정된 예약의 ID가 일치해야 합니다.")

        # 검증을 위해 데이터 조회
        async with self.pool.acquire() as conn:
            reservation_data = await conn.fetchrow(
                "SELECT * FROM reservations WHERE id = $1",
                reservation_id
            )
        self.assertEqual(reservation_data["amount"], 2, "예약 수량이 수정되어야 합니다.")

    async def test_modify_unconfirmed_if_days_left_and_user_match_success(self):
        """사용자가 미확정 예약을 수정할 때 성공적으로 이루어지는지 테스트"""
        # given
        # 테스트용 사용자 생성
        async with self.pool.acquire() as conn:
            user = await conn.fetchrow(
                "INSERT INTO users(username, password) VALUES($1, $2) RETURNING id",
                "test_user", "test_password"
            )
            user_id = user["id"]

            # 테스트용 슬롯 생성
            start_time = datetime.now(timezone.utc) + timedelta(days=7, seconds=1)  # 7일 후
            # 1 second is for delay between server and database
            end_time = start_time + timedelta(hours=1)
            slot = await conn.fetchrow(
                "INSERT INTO slots(time_range) VALUES($1) RETURNING id",
                (start_time, end_time)
            )
            slot_id = slot["id"]

            # 테스트용 예약 생성
            reservation = await conn.fetchrow(
                "INSERT INTO reservations(user_id, slot_id, amount, confirmed) VALUES($1, $2, $3, $4) RETURNING id",
                user_id, slot_id, 1, False
            )
            reservation_id = reservation["id"]

        # 수정할 예약 정보
        reservation_dto = ReservationDto(
            slot_id=slot_id,
            amount=2,
        )

        # when
        result = await self.repo.modify_unconfirmed_if_days_left_and_user_match(
            reservation_id, reservation_dto, user_id, 7
        )

        # then
        self.assertIsNotNone(result, "수정 결과가 None이면 안 됩니다.")
        self.assertEqual(result["id"], reservation_id, "수정된 예약의 ID가 일치해야 합니다.")

        # 검증을 위해 데이터 조회
        async with self.pool.acquire() as conn:
            reservation_data = await conn.fetchrow(
                "SELECT * FROM reservations WHERE id = $1",
                reservation_id
            )
        self.assertEqual(reservation_data["amount"], 2, "예약 수량이 수정되어야 합니다.")

    async def test_modify_unconfirmed_if_days_left_and_user_match_user_mismatch(self):
        """다른 사용자의 예약 수정 시 예외가 발생하는지 테스트"""
        # given
        # 테스트용 사용자 생성
        async with self.pool.acquire() as conn:
            user1 = await conn.fetchrow(
                "INSERT INTO users(username, password) VALUES($1, $2) RETURNING id",
                "test_user1", "test_password1"
            )
            user1_id = user1["id"]

            user2 = await conn.fetchrow(
                "INSERT INTO users(username, password) VALUES($1, $2) RETURNING id",
                "test_user2", "test_password2"
            )
            user2_id = user2["id"]

            # 테스트용 슬롯 생성
            start_time = datetime.now() + timedelta(days=7)  # 7일 후
            end_time = start_time + timedelta(hours=1)
            slot = await conn.fetchrow(
                "INSERT INTO slots(time_range) VALUES($1) RETURNING id",
                (start_time, end_time)
            )
            slot_id = slot["id"]

            # 테스트용 예약 생성 (user1의 예약)
            reservation = await conn.fetchrow(
                "INSERT INTO reservations(user_id, slot_id, amount, confirmed) VALUES($1, $2, $3, $4) RETURNING id",
                user1_id, slot_id, 1, False
            )
            reservation_id = reservation["id"]

        # 수정할 예약 정보
        reservation_dto = ReservationDto(
            slot_id=slot_id,
            amount=2,
        )

        # when & then (user2가 user1의 예약을 수정하려고 시도)
        with self.assertRaises(UserMismatchException):
            await self.repo.modify_unconfirmed_if_days_left_and_user_match(
                reservation_id, reservation_dto, user2_id, 7
            )

    async def test_modify_unconfirmed_if_days_left_and_user_match_already_confirmed(self):
        """이미 확정된 예약 수정 시 예외가 발생하는지 테스트"""
        # given
        # 테스트용 사용자 생성
        async with self.pool.acquire() as conn:
            user = await conn.fetchrow(
                "INSERT INTO users(username, password) VALUES($1, $2) RETURNING id",
                "test_user", "test_password"
            )
            user_id = user["id"]

            # 테스트용 슬롯 생성
            start_time = datetime.now() + timedelta(days=7)  # 7일 후
            end_time = start_time + timedelta(hours=1)
            slot = await conn.fetchrow(
                "INSERT INTO slots(time_range) VALUES($1) RETURNING id",
                (start_time, end_time)
            )
            slot_id = slot["id"]

            # 테스트용 예약 생성 (확정 상태)
            reservation = await conn.fetchrow(
                "INSERT INTO reservations(user_id, slot_id, amount, confirmed) VALUES($1, $2, $3, $4) RETURNING id",
                user_id, slot_id, 1, True
            )
            reservation_id = reservation["id"]

        # 수정할 예약 정보
        reservation_dto = ReservationDto(
            slot_id=slot_id,
            amount=2,
        )

        # when & then
        with self.assertRaises(ReservationAlreadyConfirmedException):
            await self.repo.modify_unconfirmed_if_days_left_and_user_match(
                reservation_id, reservation_dto, user_id, 7
            )

    async def test_delete_from_admin_success(self):
        """관리자가 예약 삭제가 성공적으로 이루어지는지 테스트"""
        # given
        # 테스트용 사용자 생성
        async with self.pool.acquire() as conn:
            user = await conn.fetchrow(
                "INSERT INTO users(username, password) VALUES($1, $2) RETURNING id",
                "test_user", "test_password"
            )
            user_id = user["id"]

            # 테스트용 슬롯 생성
            start_time = datetime.now()
            end_time = start_time + timedelta(hours=1)
            slot = await conn.fetchrow(
                "INSERT INTO slots(time_range) VALUES($1) RETURNING id",
                (start_time, end_time)
            )
            slot_id = slot["id"]

            # 테스트용 예약 생성
            reservation = await conn.fetchrow(
                "INSERT INTO reservations(user_id, slot_id, amount, confirmed) VALUES($1, $2, $3, $4) RETURNING id",
                user_id, slot_id, 1, False
            )
            reservation_id = reservation["id"]

        # when
        result = await self.repo.delete_from_admin(reservation_id)

        # then
        self.assertIsNotNone(result, "삭제 결과가 None이면 안 됩니다.")
        self.assertEqual(result["id"], reservation_id, "삭제된 예약의 ID가 일치해야 합니다.")

        # 검증을 위해 데이터 조회
        async with self.pool.acquire() as conn:
            reservation_data = await conn.fetchrow(
                "SELECT * FROM reservations WHERE id = $1",
                reservation_id
            )
        self.assertIsNone(reservation_data, "삭제된 예약은 조회되지 않아야 합니다.")

    async def test_delete_unconfirmed_success(self):
        """사용자가 미확정 예약 삭제가 성공적으로 이루어지는지 테스트"""
        # given
        # 테스트용 사용자 생성
        async with self.pool.acquire() as conn:
            user = await conn.fetchrow(
                "INSERT INTO users(username, password) VALUES($1, $2) RETURNING id",
                "test_user", "test_password"
            )
            user_id = user["id"]

            # 테스트용 슬롯 생성
            start_time = datetime.now() + timedelta(days=7)  # 7일 후
            end_time = start_time + timedelta(hours=1)
            slot = await conn.fetchrow(
                "INSERT INTO slots(time_range) VALUES($1) RETURNING id",
                (start_time, end_time)
            )
            slot_id = slot["id"]

            # 테스트용 예약 생성
            reservation = await conn.fetchrow(
                "INSERT INTO reservations(user_id, slot_id, amount, confirmed) VALUES($1, $2, $3, $4) RETURNING id",
                user_id, slot_id, 1, False
            )
            reservation_id = reservation["id"]

        # when
        result = await self.repo.delete_unconfirmed(reservation_id, user_id)

        # then
        self.assertIsNotNone(result, "삭제 결과가 None이면 안 됩니다.")
        self.assertEqual(result["id"], reservation_id, "삭제된 예약의 ID가 일치해야 합니다.")

        # 검증을 위해 데이터 조회
        async with self.pool.acquire() as conn:
            reservation_data = await conn.fetchrow(
                "SELECT * FROM reservations WHERE id = $1",
                reservation_id
            )
        self.assertIsNone(reservation_data, "삭제된 예약은 조회되지 않아야 합니다.")

    async def test_delete_unconfirmed_user_mismatch(self):
        """다른 사용자의 예약 삭제 시 예외가 발생하는지 테스트"""
        # given
        # 테스트용 사용자 생성
        async with self.pool.acquire() as conn:
            user1 = await conn.fetchrow(
                "INSERT INTO users(username, password) VALUES($1, $2) RETURNING id",
                "test_user1", "test_password1"
            )
            user1_id = user1["id"]

            user2 = await conn.fetchrow(
                "INSERT INTO users(username, password) VALUES($1, $2) RETURNING id",
                "test_user2", "test_password2"
            )
            user2_id = user2["id"]

            # 테스트용 슬롯 생성
            start_time = datetime.now() + timedelta(days=7)  # 7일 후
            end_time = start_time + timedelta(hours=1)
            slot = await conn.fetchrow(
                "INSERT INTO slots(time_range) VALUES($1) RETURNING id",
                (start_time, end_time)
            )
            slot_id = slot["id"]

            # 테스트용 예약 생성 (user1의 예약)
            reservation = await conn.fetchrow(
                "INSERT INTO reservations(user_id, slot_id, amount, confirmed) VALUES($1, $2, $3, $4) RETURNING id",
                user1_id, slot_id, 1, False
            )
            reservation_id = reservation["id"]

        # when & then (user2가 user1의 예약을 삭제하려고 시도)
        with self.assertRaises(UserMismatchException):
            await self.repo.delete_unconfirmed(reservation_id, user2_id)

    async def test_delete_unconfirmed_already_confirmed(self):
        """이미 확정된 예약 삭제 시 예외가 발생하는지 테스트"""
        # given
        # 테스트용 사용자 생성
        async with self.pool.acquire() as conn:
            user = await conn.fetchrow(
                "INSERT INTO users(username, password) VALUES($1, $2) RETURNING id",
                "test_user", "test_password"
            )
            user_id = user["id"]

            # 테스트용 슬롯 생성
            start_time = datetime.now() + timedelta(days=7)  # 7일 후
            end_time = start_time + timedelta(hours=1)
            slot = await conn.fetchrow(
                "INSERT INTO slots(time_range) VALUES($1) RETURNING id",
                (start_time, end_time)
            )
            slot_id = slot["id"]

            # 테스트용 예약 생성 (확정 상태)
            reservation = await conn.fetchrow(
                "INSERT INTO reservations(user_id, slot_id, amount, confirmed) VALUES($1, $2, $3, $4) RETURNING id",
                user_id, slot_id, 1, True
            )
            reservation_id = reservation["id"]

        # when & then
        with self.assertRaises(ReservationAlreadyConfirmedException):
            await self.repo.delete_unconfirmed(reservation_id, user_id)

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
    suite = unittest.TestLoader().loadTestsFromTestCase(TestReservationRepository)
    runner.run(suite) 