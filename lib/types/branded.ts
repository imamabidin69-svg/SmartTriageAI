export type Brand<T, B extends string> = T & { readonly __brand: B };

export type PatientId = Brand<string, "PatientId">;
export type TriageId = Brand<string, "TriageId">;
export type UserId = Brand<string, "UserId">;

export function toPatientId(raw: string): PatientId {
  return raw as PatientId;
}
export function toTriageId(raw: string): TriageId {
  return raw as TriageId;
}
export function toUserId(raw: string): UserId {
  return raw as UserId;
}
