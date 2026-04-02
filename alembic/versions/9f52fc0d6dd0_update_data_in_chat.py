from alembic import op
import sqlalchemy as sa

revision = '9f52fc0d6dd0'
down_revision = '7396a37f5247'

# ✅ Define ENUM
chat_type_enum = sa.Enum('group', 'direct', name='chattype')
message_type_enum = sa.Enum('text', 'image', 'file', name='messagetype')


def upgrade():
    # ✅ 1. Create ENUM first
    chat_type_enum.create(op.get_bind(), checkfirst=True)
    message_type_enum.create(op.get_bind(), checkfirst=True)

    # ✅ 2. chat_groups
    op.add_column(
        'chat_groups',
        sa.Column(
            'chat_type',
            chat_type_enum,
            nullable=False,
            server_default='group'
        )
    )

    op.add_column(
        'chat_groups',
        sa.Column(
            'is_active',
            sa.Boolean(),
            nullable=False,
            server_default=sa.text('true')
        )
    )

    # ✅ 3. chat_group_members
    op.add_column(
        'chat_group_members',
        sa.Column(
            'is_admin',
            sa.Boolean(),
            nullable=False,
            server_default=sa.text('false')
        )
    )

    # ✅ 4. chat_messages
    op.add_column(
        'chat_messages',
        sa.Column(
            'message_type',
            message_type_enum,
            nullable=False,
            server_default='text'
        )
    )

    op.add_column('chat_messages', sa.Column('content', sa.Text(), nullable=True))
    op.add_column('chat_messages', sa.Column('file_url', sa.String(500), nullable=True))
    op.add_column('chat_messages', sa.Column('file_name', sa.String(255), nullable=True))
    op.add_column('chat_messages', sa.Column('file_size', sa.Integer(), nullable=True))

    op.add_column(
        'chat_messages',
        sa.Column(
            'is_deleted',
            sa.Boolean(),
            nullable=False,
            server_default=sa.text('false')  # ✅ FIXED
        )
    )

    # ✅ 5. drop old column
    op.drop_column('chat_messages', 'message_text')


def downgrade():
    # restore old column
    op.add_column(
        'chat_messages',
        sa.Column('message_text', sa.Text(), nullable=False)
    )

    # drop new columns
    op.drop_column('chat_messages', 'is_deleted')
    op.drop_column('chat_messages', 'file_size')
    op.drop_column('chat_messages', 'file_name')
    op.drop_column('chat_messages', 'file_url')
    op.drop_column('chat_messages', 'content')
    op.drop_column('chat_messages', 'message_type')

    op.drop_column('chat_group_members', 'is_admin')

    op.drop_column('chat_groups', 'is_active')
    op.drop_column('chat_groups', 'chat_type')

    # drop ENUM
    message_type_enum.drop(op.get_bind(), checkfirst=True)
    chat_type_enum.drop(op.get_bind(), checkfirst=True)