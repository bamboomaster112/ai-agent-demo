export interface MigrationSession {
  id: string;
  title: string | null;
  source_type: string;
  source_platform: string | null;
  source_format: string | null;
  config_type: string | null;
  detection_confidence: number | null;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface Message {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  metadata: Record<string, unknown>;
  created_at: string;
}

export interface Workflow {
  id: string;
  filename: string;
  yaml_content: string;
  notes: Array<{ level: string; text: string }>;
  version: number;
  created_at: string;
}

export interface SessionDetail {
  session: MigrationSession;
  messages: Message[];
  workflows: Workflow[];
}

export interface DetectionResult {
  source_platform: string;
  source_format: string;
  config_type: string;
  confidence: number;
  method: string;
  matched_patterns: string[];
}

export type SourceType =
  | "teamcity_kotlin"
  | "teamcity_xml"
  | "teamcity_json"
  | "jenkins";
