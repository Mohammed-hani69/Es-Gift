"""إضافة حقول التحقق من البريد الإلكتروني

Revision ID: add_email_verification_fields
Revises: 
Create Date: 2024-12-28 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision = 'add_email_verification_fields'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    """إضافة حقول التحقق من البريد الإلكتروني إلى جدول User"""
    
    # إضافة الحقول الجديدة
    op.add_column('user', sa.Column('email_verification_token', sa.String(100), nullable=True))
    op.add_column('user', sa.Column('email_verification_sent_at', sa.DateTime(), nullable=True))
    
    print("تم إضافة حقول التحقق من البريد الإلكتروني بنجاح")

def downgrade():
    """إزالة حقول التحقق من البريد الإلكتروني من جدول User"""
    
    # إزالة الحقول
    op.drop_column('user', 'email_verification_sent_at')
    op.drop_column('user', 'email_verification_token')
    
    print("تم إزالة حقول التحقق من البريد الإلكتروني")
