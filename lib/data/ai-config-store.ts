import "server-only";
import type { AiConfig } from "@/lib/schemas/ai-config.schema";

let config: AiConfig = {
  versiModel: "v1.2.0-rule-based",
  ambangKritis: 6,
  ambangTinggi: 4,
  ambangSedang: 2,
  wajibkanValidasiDpjUntukKritis: true,
};

export function getAiConfig(): AiConfig {
  return config;
}

export function setAiConfig(next: AiConfig): AiConfig {
  config = next;
  return config;
}
