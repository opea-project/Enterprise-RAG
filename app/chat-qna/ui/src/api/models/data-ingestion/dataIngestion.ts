export interface DataIngestionRequest {
  files?: { filename: string; data64: string }[];
  links?: string[];
}
