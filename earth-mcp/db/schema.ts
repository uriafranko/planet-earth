import { pgTable, uuid, text, jsonb, timestamp, vector, integer } from 'drizzle-orm/pg-core';

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

// --- Audit Logging Tables ---

export const audits = pgTable('audits', {
  id: uuid('id').primaryKey().defaultRandom(),
  query: text('query').notNull(),
  total_result_count: integer('total_result_count').notNull(),
  created_at: timestamp('created_at', { withTimezone: true }).defaultNow().notNull(),
});

export const auditResults = pgTable('audit_results', {
  id: uuid('id').primaryKey().defaultRandom(),
  audit_id: uuid('audit_id').notNull().references(() => audits.id),
  schema_id: uuid('schema_id').notNull(),
  endpoint_id: uuid('endpoint_id').notNull(),
  result_count: integer('result_count').notNull(),
});


