import logging
import sys
import unittest

from dotenv import load_dotenv

from app.dependencies.config import database
from app.repositories.user.dbimpl import NoSuchUserException, UserNameAlreadyExistsException, UserRepositoryImpl


class TestUserRepositoryImpl(unittest.IsolatedAsyncioTestCase):
    """사용자 레포지토리 구현체에 대한 테스트 클래스"""

    # 테스트 클래스 로거 설정
    logger = logging.getLogger('TestUserRepositoryImpl')

    async def asyncSetUp(self):
        """각 테스트 실행 전 데이터베이스 연결 및 테스트 데이터 초기화"""
        self.logger.info("테스트 환경 설정 시작")
        load_dotenv()
        self.logger.info("데이터베이스 연결 중...")
        await database.connect()
        self.pool = database.get_pool()
        self.logger.info("UserRepositoryImpl 인스턴스 생성 중...")
        self.repo = UserRepositoryImpl(self.pool)

        # 테스트 데이터 정리
        self.logger.info("이전 테스트 데이터 정리 중...")
        async with self.pool.acquire() as conn:
            await conn.execute("DELETE FROM users WHERE username LIKE 'test_user%'")
        self.logger.info("테스트 환경 설정 완료")

    async def asyncTearDown(self):
        """각 테스트 실행 후 테스트 데이터 정리 및 데이터베이스 연결 해제"""
        self.logger.info("테스트 정리 시작")
        # 테스트 데이터 정리
        self.logger.info("테스트 데이터 삭제 중...")
        async with self.pool.acquire() as conn:
            await conn.execute("DELETE FROM users WHERE username LIKE 'test_user%'")
        self.logger.info("데이터베이스 연결 해제 중...")
        await database.disconnect()
        self.logger.info("테스트 정리 완료")

    async def test_insert_success(self):
        """사용자 등록이 성공적으로 이루어지는지 테스트"""
        # given
        username = "test_user1"
        password = "hashed_password1"

        # when
        result = await self.repo.insert(username, password)

        # then
        self.assertIsNotNone(result, "삽입 결과가 None이면 안 됩니다.")
        self.assertIn("id", result, "삽입 결과에 'id' 필드가 포함되어야 합니다.")

        # 검증을 위해 데이터 조회
        async with self.pool.acquire() as conn:
            user = await conn.fetchrow("SELECT * FROM users WHERE username = $1", username)
        self.assertEqual(user["username"], username, f"저장된 사용자명이 {username}이어야 합니다.")
        self.assertEqual(user["password"], password, "저장된 비밀번호가 입력한 값과 일치해야 합니다.")

    async def test_insert_duplicate_username(self):
        """중복된 사용자명으로 등록 시 예외가 발생하는지 테스트"""
        # given
        username = "test_user2"
        password = "hashed_password2"

        # 첫 번째 삽입
        await self.repo.insert(username, password)

        # when & then - 두 번째 삽입 시 예외 발생해야 함
        with self.assertRaises(UserNameAlreadyExistsException) as context:
            await self.repo.insert(username, "different_password")

        self.assertEqual(context.exception.username, username, "예외에 포함된 사용자명이 입력한 값과 일치해야 합니다.")

    async def test_find_success(self):
        """사용자명으로 사용자 조회가 성공적으로 이루어지는지 테스트"""
        # given
        username = "test_user3"
        password = "hashed_password3"
        await self.repo.insert(username, password)

        # when
        user = await self.repo.find(username)

        # then
        self.assertIsNotNone(user, "조회된 사용자가 None이면 안 됩니다.")
        self.assertEqual(user["username"], username, f"조회된 사용자명이 {username}이어야 합니다.")
        self.assertEqual(user["password"], password, "조회된 비밀번호가 입력한 값과 일치해야 합니다.")

    async def test_find_non_existent_user(self):
        """존재하지 않는 사용자 조회 시 예외가 발생하는지 테스트"""
        # given
        username = "non_existent_user"

        # when & then
        with self.assertRaises(NoSuchUserException) as context:
            await self.repo.find(username)

        self.assertIn(f"username = {username}", context.exception.message, "예외 메시지에 사용자명 조건이 포함되어야 합니다.")

    async def test_update_password_success(self):
        """비밀번호 업데이트가 성공적으로 이루어지는지 테스트"""
        # given
        username = "test_user4"
        old_password = "old_hashed_password"
        new_password = "new_hashed_password"

        # 사용자 생성
        await self.repo.insert(username, old_password)

        # when
        result = await self.repo.update_password(username, new_password)

        # then
        self.assertIsNotNone(result, "비밀번호 업데이트 결과가 None이면 안 됩니다.")

        # 변경된 비밀번호 확인
        user = await self.repo.find(username)
        self.assertEqual(user["password"], new_password, "변경된 비밀번호가 입력한 새 비밀번호와 일치해야 합니다.")

    async def test_update_password_non_existent_user(self):
        """존재하지 않는 사용자의 비밀번호 업데이트 시 예외가 발생하는지 테스트"""
        # given
        username = "non_existent_user"
        password = "new_password"

        # when & then
        with self.assertRaises(NoSuchUserException) as context:
            await self.repo.update_password(username, password)

        self.assertIn(f"username = {username}", context.exception.message)

    async def test_delete_by_username_success(self):
        """사용자명으로 사용자 삭제가 성공적으로 이루어지는지 테스트"""
        # given
        username = "test_user5"
        password = "hashed_password5"

        # 사용자 생성
        await self.repo.insert(username, password)

        # when
        result = await self.repo.delete_by_username(username)

        # then
        self.assertIsNotNone(result, "사용자 삭제 결과가 None이면 안 됩니다.")

        # 사용자가 정말 삭제되었는지 확인
        async with self.pool.acquire() as conn:
            user = await conn.fetchrow("SELECT * FROM users WHERE username = $1", username)
        self.assertIsNone(user, "삭제된 사용자는 조회되지 않아야 합니다.")

    async def test_delete_by_username_non_existent_user(self):
        """존재하지 않는 사용자명으로 삭제 시 예외가 발생하는지 테스트"""
        # given
        username = "non_existent_user"

        # when & then
        with self.assertRaises(NoSuchUserException) as context:
            await self.repo.delete_by_username(username)

        self.assertIn(f"username = {username}", context.exception.message)

    async def test_delete_by_id_success(self):
        """사용자 ID로 사용자 삭제가 성공적으로 이루어지는지 테스트"""
        # given
        username = "test_user6"
        password = "hashed_password6"

        # 사용자 생성
        result = await self.repo.insert(username, password)
        user_id = result["id"]

        # when
        delete_result = await self.repo.delete(user_id)

        # then
        self.assertIsNotNone(delete_result, "ID로 사용자 삭제 결과가 None이면 안 됩니다.")
        self.assertEqual(delete_result["id"], user_id, "삭제된 사용자의 ID가 원래 사용자 ID와 일치해야 합니다.")

        # 사용자가 정말 삭제되었는지 확인
        async with self.pool.acquire() as conn:
            user = await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
        self.assertIsNone(user)

    async def test_delete_by_id_non_existent_user(self):
        """존재하지 않는 사용자 ID로 삭제 시 예외가 발생하는지 테스트"""
        # given
        non_existent_id = 999999  # 존재하지 않는 ID

        # when & then
        with self.assertRaises(NoSuchUserException) as context:
            await self.repo.delete(non_existent_id)

        self.assertIn(f"id = {non_existent_id}", context.exception.message)


if __name__ == "__main__":
    # 로그 설정
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        stream=sys.stdout
    )

    # TestRunner 설정
    runner = unittest.TextTestRunner(verbosity=3)

    # 테스트 실행
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUserRepositoryImpl)
    runner.run(suite)
