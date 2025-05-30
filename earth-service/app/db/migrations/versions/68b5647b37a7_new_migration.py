"""New migration

Revision ID: 68b5647b37a7
Revises:
Create Date: 2025-04-12 11:32:34.205725

"""
import pgvector.sqlalchemy
import sqlalchemy as sa
import sqlmodel
from alembic import op

# revision identifiers, used by Alembic.
revision = "68b5647b37a7"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table("schemas",
    sa.Column("id", sa.Uuid(), nullable=False),
    sa.Column("created_at", sa.DateTime(), server_default="now()", nullable=False),
    sa.Column("title", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column("version", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column("checksum", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column("status", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.PrimaryKeyConstraint("id")
    )
    op.create_index(op.f("ix_schemas_checksum"), "schemas", ["checksum"], unique=True)
    op.create_index(op.f("ix_schemas_id"), "schemas", ["id"], unique=False)
    op.create_index(op.f("ix_schemas_status"), "schemas", ["status"], unique=False)
    op.create_index(op.f("ix_schemas_title"), "schemas", ["title"], unique=False)
    op.create_index(op.f("ix_schemas_version"), "schemas", ["version"], unique=False)
    op.create_table("endpoints",
    sa.Column("id", sa.Uuid(), nullable=False),
    sa.Column("created_at", sa.DateTime(), server_default="now()", nullable=False),
    sa.Column("embedding_vector", pgvector.sqlalchemy.vector.VECTOR(dim=384), nullable=True),
    sa.Column("schema_id", sa.Uuid(), nullable=False),
    sa.Column("path", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column("method", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column("operation_id", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column("hash", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column("deleted_at", sa.DateTime(), nullable=True),
    sa.Column("summary", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column("description", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column("tags", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column("spec", sa.JSON(), nullable=True),
    sa.ForeignKeyConstraint(["schema_id"], ["schemas.id"] ),
    sa.PrimaryKeyConstraint("id"),
    sa.UniqueConstraint("schema_id", "path", "method", name="ux_schema_path_method")
    )
    op.create_index(op.f("ix_endpoints_hash"), "endpoints", ["hash"], unique=False)
    op.create_index(op.f("ix_endpoints_id"), "endpoints", ["id"], unique=False)
    op.create_index(op.f("ix_endpoints_method"), "endpoints", ["method"], unique=False)
    op.create_index(op.f("ix_endpoints_operation_id"), "endpoints", ["operation_id"], unique=False)
    op.create_index(op.f("ix_endpoints_path"), "endpoints", ["path"], unique=False)
    op.create_index(op.f("ix_endpoints_schema_id"), "endpoints", ["schema_id"], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f("ix_endpoints_schema_id"), table_name="endpoints")
    op.drop_index(op.f("ix_endpoints_path"), table_name="endpoints")
    op.drop_index(op.f("ix_endpoints_operation_id"), table_name="endpoints")
    op.drop_index(op.f("ix_endpoints_method"), table_name="endpoints")
    op.drop_index(op.f("ix_endpoints_id"), table_name="endpoints")
    op.drop_index(op.f("ix_endpoints_hash"), table_name="endpoints")
    op.drop_table("endpoints")
    op.drop_index(op.f("ix_schemas_version"), table_name="schemas")
    op.drop_index(op.f("ix_schemas_title"), table_name="schemas")
    op.drop_index(op.f("ix_schemas_status"), table_name="schemas")
    op.drop_index(op.f("ix_schemas_id"), table_name="schemas")
    op.drop_index(op.f("ix_schemas_checksum"), table_name="schemas")
    op.drop_table("schemas")
    # ### end Alembic commands ###
