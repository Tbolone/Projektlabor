"""package courier assignment

A csomagokhoz eltároljuk, melyik futár végzi a felvételt, illetve a kiszállítást.
Korábban ez sehol nem szerepelt, így a futár nem tudta, mi az ő feladata.

Revision ID: b2c7a91d4e10
Revises: f14eded8be6a
Create Date: 2026-10-27

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c7a91d4e10'
down_revision: Union[str, Sequence[str], None] = 'f14eded8be6a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('packages', sa.Column('pickup_courier_id', sa.Integer(), nullable=True))
    op.add_column('packages', sa.Column('delivery_courier_id', sa.Integer(), nullable=True))

    op.create_index(
        op.f('ix_packages_pickup_courier_id'), 'packages', ['pickup_courier_id'], unique=False
    )
    op.create_index(
        op.f('ix_packages_delivery_courier_id'), 'packages', ['delivery_courier_id'], unique=False
    )

    op.create_foreign_key(
        'fk_packages_pickup_courier_id', 'packages', 'couriers', ['pickup_courier_id'], ['id']
    )
    op.create_foreign_key(
        'fk_packages_delivery_courier_id', 'packages', 'couriers', ['delivery_courier_id'], ['id']
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('fk_packages_delivery_courier_id', 'packages', type_='foreignkey')
    op.drop_constraint('fk_packages_pickup_courier_id', 'packages', type_='foreignkey')
    op.drop_index(op.f('ix_packages_delivery_courier_id'), table_name='packages')
    op.drop_index(op.f('ix_packages_pickup_courier_id'), table_name='packages')
    op.drop_column('packages', 'delivery_courier_id')
    op.drop_column('packages', 'pickup_courier_id')
