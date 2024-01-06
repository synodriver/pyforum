"""add login ip

Revision ID: 5779d4df257a
Revises: f1ab7b3ed201
Create Date: 2024-01-02 20:30:26.441739

"""
from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "5779d4df257a"
down_revision: Union[str, None] = "f1ab7b3ed201"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "user", sa.Column("last_ip", sqlmodel.sql.sqltypes.AutoString(), nullable=True)
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("user", "last_ip")
    # ### end Alembic commands ###