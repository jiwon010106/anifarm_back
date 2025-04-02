from sqlalchemy import text
from datetime import datetime
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

class CommentService:
    def __init__(self, db):
        self.db = db

    async def get_user_comments(self, user_email):
        try:
            query = text("""
                SELECT c.*, w.title as post_title, w.community_type
                FROM comments c
                JOIN write w ON c.post_id = w.post_id
                JOIN auth a ON c.user_id = a.user_id
                WHERE a.email = :email
                ORDER BY c.created_at DESC
            """)
            
            result = self.db.execute(query, {"email": user_email})
            comments = result.fetchall()
            
            return [{
                "comment_id": comment.comment_id,
                "post_id": comment.post_id,
                "content": comment.content,
                "created_at": comment.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                "post_title": comment.post_title,
                "community_type": comment.community_type
            } for comment in comments]
        except Exception as e:
            logger.error(f"사용자 댓글 조회 중 오류 발생: {str(e)}")
            raise

    async def get_post_comments(self, post_id):
        try:
            query = text("""
                WITH RECURSIVE CommentHierarchy AS (
                    -- 부모 댓글 조회
                    SELECT 
                        c.comment_id,
                        c.post_id,
                        c.user_id,
                        c.content,
                        c.created_at,
                        c.community_type,
                        c.parent_id,
                        a.email,
                        0 as depth,
                        CAST(c.comment_id AS VARCHAR) as path
                    FROM comments c
                    JOIN auth a ON c.user_id = a.user_id
                    WHERE c.post_id = :post_id AND c.parent_id IS NULL
                    
                    UNION ALL
                    
                    -- 대댓글 조회
                    SELECT 
                        c.comment_id,
                        c.post_id,
                        c.user_id,
                        c.content,
                        c.created_at,
                        c.community_type,
                        c.parent_id,
                        a.email,
                        ch.depth + 1,
                        ch.path || ',' || CAST(c.comment_id AS VARCHAR)
                    FROM comments c
                    JOIN auth a ON c.user_id = a.user_id
                    JOIN CommentHierarchy ch ON c.parent_id = ch.comment_id
                )
                SELECT * FROM CommentHierarchy
                ORDER BY path, created_at
            """)
            
            result = self.db.execute(query, {"post_id": post_id})
            comments = result.fetchall()
            
            return [{
                "comment_id": comment.comment_id,
                "post_id": comment.post_id,
                "user_id": comment.user_id,
                "content": comment.content,
                "created_at": comment.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                "community_type": comment.community_type,
                "parent_id": comment.parent_id,
                "email": comment.email,
                "depth": comment.depth
            } for comment in comments]
        except Exception as e:
            logger.error(f"게시글 댓글 조회 중 오류 발생: {str(e)}")
            raise

    async def create_comment(self, comment_data):
        try:
            # 사용자 ID 조회
            user_query = text("SELECT user_id FROM auth WHERE email = :email")
            user_result = self.db.execute(user_query, {"email": comment_data.user_email})
            user_id = user_result.scalar()
            
            if not user_id:
                raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")

            # 게시글 존재 여부와 community_type 확인
            post_query = text("""
                SELECT post_id, community_type 
                FROM write 
                WHERE post_id = :post_id
            """)
            post_result = self.db.execute(post_query, {"post_id": comment_data.post_id}).fetchone()
            
            if not post_result:
                raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다")

            # 댓글 생성
            insert_query = text("""
                INSERT INTO comments 
                (post_id, user_id, content, created_at, community_type, parent_id) 
                VALUES 
                (:post_id, :user_id, :content, :created_at, :community_type, :parent_id)
                RETURNING comment_id, post_id, user_id, content, created_at, community_type, parent_id
            """)
            
            result = self.db.execute(
                insert_query,
                {
                    "post_id": comment_data.post_id,
                    "user_id": user_id,
                    "content": comment_data.content,
                    "created_at": datetime.now(),
                    "community_type": post_result.community_type,
                    "parent_id": getattr(comment_data, 'parent_id', None)  # 대댓글인 경우 부모 댓글 ID
                }
            )
            
            # 트랜잭션 커밋 추가
            self.db.commit()
            
            new_comment = result.fetchone()
            
            return {
                "comment_id": new_comment.comment_id,
                "post_id": new_comment.post_id,
                "user_id": new_comment.user_id,
                "content": new_comment.content,
                "created_at": new_comment.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                "community_type": new_comment.community_type,
                "parent_id": new_comment.parent_id,
                "email": comment_data.user_email
            }
        except Exception as e:
            self.db.rollback()  # 롤백 추가
            logger.error(f"댓글 생성 중 오류 발생: {str(e)}")
            raise

    async def update_comment(self, comment_id, content, user_email):
        try:
            # 사용자 ID 조회
            user_query = text("SELECT user_id FROM auth WHERE email = :email")
            user_result = self.db.execute(user_query, {"email": user_email})
            user_id = user_result.scalar()
            
            if not user_id:
                raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")

            # 댓글 권한 확인
            comment_query = text("""
                SELECT c.* FROM comments c
                WHERE c.comment_id = :comment_id AND c.user_id = :user_id
            """)
            if not self.db.execute(comment_query, {
                "comment_id": comment_id,
                "user_id": user_id
            }).fetchone():
                raise HTTPException(status_code=403, detail="댓글 수정 권한이 없습니다")

            # 댓글 수정
            update_query = text("""
                UPDATE comments 
                SET content = :content
                WHERE comment_id = :comment_id 
                RETURNING comment_id, post_id, user_id, content, created_at
            """)
            
            result = self.db.execute(
                update_query,
                {"comment_id": comment_id, "content": content}
            )
            
            updated_comment = result.fetchone()
            
            # 트랜잭션 커밋 추가
            self.db.commit()
            
            return {
                "comment_id": updated_comment.comment_id,
                "post_id": updated_comment.post_id,
                "user_id": updated_comment.user_id,
                "content": updated_comment.content,
                "created_at": updated_comment.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                "email": user_email
            }
        except Exception as e:
            self.db.rollback()  # 에러 발생 시 롤백 추가
            logger.error(f"댓글 수정 중 오류 발생: {str(e)}")
            raise

    async def delete_comment(self, comment_id, user_email):
        try:
            # 사용자 ID 조회
            user_query = text("SELECT user_id FROM auth WHERE email = :email")
            user_result = self.db.execute(user_query, {"email": user_email})
            user_id = user_result.scalar()
            
            if not user_id:
                raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")

            # 댓글 권한 확인
            comment_query = text("""
                SELECT c.* FROM comments c
                WHERE c.comment_id = :comment_id AND c.user_id = :user_id
            """)
            if not self.db.execute(comment_query, {
                "comment_id": comment_id,
                "user_id": user_id
            }).fetchone():
                raise HTTPException(status_code=403, detail="댓글 삭제 권한이 없습니다")

            # 댓글 삭제
            delete_query = text("""
                DELETE FROM comments 
                WHERE comment_id = :comment_id 
                RETURNING comment_id
            """)
            
            result = self.db.execute(delete_query, {"comment_id": comment_id})
            
            if result.rowcount == 0:
                raise HTTPException(status_code=404, detail="댓글을 찾을 수 없습니다")
            
            # 트랜잭션 커밋 추가
            self.db.commit()
            
            return comment_id
        except Exception as e:
            # 롤백 추가
            self.db.rollback()
            logger.error(f"댓글 삭제 중 오류 발생: {str(e)}")
            raise 