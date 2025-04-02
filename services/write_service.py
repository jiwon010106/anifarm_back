from sqlalchemy import text
from datetime import datetime
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

class WriteService:
    def __init__(self, db):
        self.db = db

    async def create_post(self, post_data, user_email):
        try:
            # 사용자 ID 조회
            user_query = text("SELECT user_id FROM auth WHERE email = :email")
            user_result = self.db.execute(user_query, {"email": user_email})
            user_id = user_result.scalar()
            
            if not user_id:
                raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")

            # 게시글 작성
            current_time = datetime.now()
            query = text("""
                INSERT INTO write (user_id, title, content, date, category, community_type)
                VALUES (:user_id, :title, :content, :date, :category, :community_type)
                RETURNING post_id, user_id, title, content, date, category, community_type
            """)
            
            result = self.db.execute(
                query,
                {
                    "user_id": user_id,
                    "title": post_data.title,
                    "content": post_data.content,
                    "date": current_time,
                    "category": post_data.category,
                    "community_type": post_data.community_type
                }
            )
            
            # 트랜잭션 커밋 추가
            self.db.commit()
            
            new_post = result.fetchone()
            
            return {
                "post_id": new_post.post_id,
                "user_id": new_post.user_id,
                "title": new_post.title,
                "content": new_post.content,
                "date": new_post.date.strftime('%Y-%m-%d %H:%M:%S'),
                "category": new_post.category,
                "community_type": new_post.community_type,
                "email": user_email
            }
        except Exception as e:
            self.db.rollback()  # 롤백 추가
            logger.error(f"게시글 작성 중 오류 발생: {str(e)}")
            raise

    async def get_post(self, post_id):
        try:
            query = text("""
                SELECT w.*, a.email 
                FROM write w 
                JOIN auth a ON w.user_id = a.user_id 
                WHERE w.post_id = :post_id
            """)
            
            result = self.db.execute(query, {"post_id": post_id})
            post = result.fetchone()
            
            if not post:
                raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다")
            
            return {
                "post_id": post.post_id,
                "user_id": post.user_id,
                "title": post.title,
                "content": post.content,
                "date": post.date.strftime('%Y-%m-%d %H:%M:%S'),
                "category": post.category,
                "community_type": post.community_type,
                "email": post.email
            }
        except Exception as e:
            logger.error(f"게시글 조회 중 오류 발생: {str(e)}")
            raise

    async def get_community_posts(self, community_type):
        try:
            query = text("""
                SELECT w.*, u.email 
                FROM write w 
                JOIN auth u ON w.user_id = u.user_id 
                WHERE w.community_type = :community_type 
                ORDER BY w.date DESC
            """)
            
            result = self.db.execute(query, {"community_type": community_type})
            posts = result.fetchall()
            
            return [{
                "post_id": post.post_id,
                "user_id": post.user_id,
                "title": post.title,
                "content": post.content,
                "date": post.date.strftime('%Y-%m-%d %H:%M:%S'),
                "category": post.category,
                "community_type": post.community_type,
                "email": post.email
            } for post in posts]
        except Exception as e:
            logger.error(f"커뮤니티 게시글 조회 중 오류 발생: {str(e)}")
            raise

    async def update_post(self, post_id, post_data, user_email):
        try:
            # 사용자 ID 조회
            user_query = text("SELECT user_id FROM auth WHERE email = :email")
            user_result = self.db.execute(user_query, {"email": user_email})
            user_id = user_result.scalar()
            
            if not user_id:
                raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")

            # 게시글 권한 확인
            post_query = text("""
                SELECT * FROM write 
                WHERE post_id = :post_id AND user_id = :user_id
            """)
            if not self.db.execute(post_query, {
                "post_id": post_id,
                "user_id": user_id
            }).fetchone():
                raise HTTPException(status_code=403, detail="게시글 수정 권한이 없습니다")

            # 게시글 수정
            update_query = text("""
                UPDATE write 
                SET title = COALESCE(:title, title),
                    content = COALESCE(:content, content),
                    category = COALESCE(:category, category),
                    community_type = COALESCE(:community_type, community_type)
                WHERE post_id = :post_id 
                RETURNING *
            """)
            
            result = self.db.execute(
                update_query,
                {
                    "post_id": post_id,
                    "title": post_data.title,
                    "content": post_data.content,
                    "category": post_data.category,
                    "community_type": post_data.community_type
                }
            )
            
            # 트랜잭션 커밋 추가
            self.db.commit()
            
            updated_post = result.fetchone()
            
            return {
                "post_id": updated_post.post_id,
                "user_id": updated_post.user_id,
                "title": updated_post.title,
                "content": updated_post.content,
                "date": updated_post.date.strftime('%Y-%m-%d %H:%M:%S'),
                "category": updated_post.category,
                "community_type": updated_post.community_type,
                "email": user_email
            }
        except Exception as e:
            self.db.rollback()  # 롤백 추가
            logger.error(f"게시글 수정 중 오류 발생: {str(e)}")
            raise

    async def delete_post(self, post_id, user_email):
        try:
            # 사용자 ID 조회
            user_query = text("SELECT user_id FROM auth WHERE email = :email")
            user_result = self.db.execute(user_query, {"email": user_email})
            user_id = user_result.scalar()
            
            if not user_id:
                raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")

            # 게시글 권한 확인
            post_query = text("""
                SELECT * FROM write 
                WHERE post_id = :post_id AND user_id = :user_id
            """)
            if not self.db.execute(post_query, {
                "post_id": post_id,
                "user_id": user_id
            }).fetchone():
                raise HTTPException(status_code=403, detail="게시글 삭제 권한이 없습니다")

            # 연관된 댓글 삭제
            self.db.execute(
                text("DELETE FROM comments WHERE post_id = :post_id"),
                {"post_id": post_id}
            )

            # 게시글 삭제
            delete_query = text("""
                DELETE FROM write 
                WHERE post_id = :post_id 
                RETURNING post_id
            """)
            
            result = self.db.execute(delete_query, {"post_id": post_id})
            
            # 트랜잭션 커밋 추가
            self.db.commit()
            
            if result.rowcount == 0:
                raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다")
            
            return post_id
        except Exception as e:
            self.db.rollback()  # 롤백 추가
            logger.error(f"게시글 삭제 중 오류 발생: {str(e)}")
            raise

    async def get_user_posts(self, user_email):
        try:
            query = text("""
                SELECT w.*, a.email 
                FROM write w 
                JOIN auth a ON w.user_id = a.user_id 
                WHERE a.email = :email 
                ORDER BY w.date DESC
            """)
            
            result = self.db.execute(query, {"email": user_email})
            posts = result.fetchall()
            
            return [{
                "post_id": post.post_id,
                "title": post.title,
                "content": post.content,
                "date": post.date.strftime('%Y-%m-%d %H:%M:%S'),
                "category": post.category,
                "community_type": post.community_type,
                "email": post.email
            } for post in posts]
        except Exception as e:
            logger.error(f"사용자 게시글 조회 중 오류 발생: {str(e)}")
            raise 