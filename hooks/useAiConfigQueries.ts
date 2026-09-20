"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { fetchAiConfig, updateAiConfig } from "@/lib/api-client";
import type { AiConfig } from "@/lib/schemas/ai-config.schema";

export const aiConfigKey = () => ["ai-config"] as const;

export function useAiConfigQuery() {
  return useQuery({
    queryKey: aiConfigKey(),
    queryFn: fetchAiConfig,
  });
}

export function useUpdateAiConfigMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: AiConfig) => updateAiConfig(input),
    onSuccess: (data) => {
      queryClient.setQueryData(aiConfigKey(), data);
    },
  });
}
