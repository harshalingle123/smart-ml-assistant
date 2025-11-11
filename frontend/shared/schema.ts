import { sql } from "drizzle-orm";
import { pgTable, text, varchar, integer, timestamp, jsonb } from "drizzle-orm/pg-core";
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod";

export const users = pgTable("users", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  username: text("username").notNull().unique(),
  password: text("password").notNull(),
  currentPlan: text("current_plan").notNull().default("free"),
  queriesUsed: integer("queries_used").notNull().default(0),
  fineTuneJobs: integer("fine_tune_jobs").notNull().default(0),
  datasetsCount: integer("datasets_count").notNull().default(0),
  billingCycle: text("billing_cycle"),
});

export const chats = pgTable("chats", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  userId: varchar("user_id").notNull(),
  title: text("title").notNull(),
  modelId: varchar("model_id"),
  datasetId: varchar("dataset_id"),
  lastUpdated: timestamp("last_updated").notNull().defaultNow(),
});

export const messages = pgTable("messages", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  chatId: varchar("chat_id").notNull(),
  role: text("role").notNull(),
  content: text("content").notNull(),
  queryType: text("query_type"),
  charts: jsonb("charts"),
  timestamp: timestamp("timestamp").notNull().defaultNow(),
});

export const models = pgTable("models", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  userId: varchar("user_id").notNull(),
  name: text("name").notNull(),
  baseModel: text("base_model").notNull(),
  version: text("version").notNull(),
  accuracy: text("accuracy"),
  f1Score: text("f1_score"),
  loss: text("loss"),
  status: text("status").notNull().default("ready"),
  datasetId: varchar("dataset_id"),
  createdAt: timestamp("created_at").notNull().defaultNow(),
});

export const datasets = pgTable("datasets", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  userId: varchar("user_id").notNull(),
  name: text("name").notNull(),
  fileName: text("file_name").notNull(),
  rowCount: integer("row_count").notNull(),
  columnCount: integer("column_count").notNull(),
  fileSize: integer("file_size").notNull(),
  status: text("status").notNull().default("processing"),
  previewData: jsonb("preview_data"),
  uploadedAt: timestamp("uploaded_at").notNull().defaultNow(),
});

export const fineTuneJobs = pgTable("fine_tune_jobs", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  userId: varchar("user_id").notNull(),
  modelId: varchar("model_id"),
  datasetId: varchar("dataset_id").notNull(),
  baseModel: text("base_model").notNull(),
  status: text("status").notNull().default("preparing"),
  progress: integer("progress").notNull().default(0),
  currentStep: text("current_step"),
  logs: text("logs"),
  createdAt: timestamp("created_at").notNull().defaultNow(),
  completedAt: timestamp("completed_at"),
});

export const apiKeys = pgTable("api_keys", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  userId: varchar("user_id").notNull(),
  modelId: varchar("model_id").notNull(),
  key: text("key").notNull().unique(),
  name: text("name").notNull(),
  createdAt: timestamp("created_at").notNull().defaultNow(),
});

export const insertUserSchema = createInsertSchema(users).pick({
  username: true,
  password: true,
});

export const insertChatSchema = createInsertSchema(chats).omit({ id: true, lastUpdated: true });
export const insertMessageSchema = createInsertSchema(messages).omit({ id: true, timestamp: true });
export const insertModelSchema = createInsertSchema(models).omit({ id: true, createdAt: true });
export const insertDatasetSchema = createInsertSchema(datasets).omit({ id: true, uploadedAt: true });
export const insertFineTuneJobSchema = createInsertSchema(fineTuneJobs).omit({ id: true, createdAt: true, completedAt: true });
export const insertApiKeySchema = createInsertSchema(apiKeys).omit({ id: true, createdAt: true });

export type InsertUser = z.infer<typeof insertUserSchema>;
export type User = typeof users.$inferSelect;
export type Chat = typeof chats.$inferSelect;
export type InsertChat = z.infer<typeof insertChatSchema>;
export type Message = typeof messages.$inferSelect;
export type InsertMessage = z.infer<typeof insertMessageSchema>;
export type Model = typeof models.$inferSelect;
export type InsertModel = z.infer<typeof insertModelSchema>;
export type Dataset = typeof datasets.$inferSelect;
export type InsertDataset = z.infer<typeof insertDatasetSchema>;
export type FineTuneJob = typeof fineTuneJobs.$inferSelect;
export type InsertFineTuneJob = z.infer<typeof insertFineTuneJobSchema>;
export type ApiKey = typeof apiKeys.$inferSelect;
export type InsertApiKey = z.infer<typeof insertApiKeySchema>;
