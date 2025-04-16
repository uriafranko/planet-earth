import { pgTable, uuid, text, jsonb, timestamp, vector } from 'drizzle-orm/pg-core';

export const endpoints = pgTable('endpoints', {
  id: uuid('id').primaryKey(),
  schema_id: uuid('schema_id').notNull(),
  path: text('path').notNull(),
  method: text('method').notNull(),
  operation_id: text('operation_id'),
  hash: text('hash').notNull(),
  deleted_at: timestamp('deleted_at', { withTimezone: true }),
  summary: text('summary'),
  description: text('description'),
  tags: text('tags'), // JSON string
  spec: jsonb('spec'),
  embedding_vector: vector('embedding_vector', { dimensions: 768 }).notNull(),
});
