// Carries one model call over Firebase AI Logic, with the Agent Platform Gemini API as the backend.
// Agent Platform is billed to the project's Cloud Billing account (and its credits); the Gemini
// Developer API would need its own prepaid balance in AI Studio (see DECISIONS, entry 120).
// Loaded only when a screen first asks the AI for something, so the SDK is not in the first download.
//
// The calls follow the type definitions of firebase 13.0.0 (@firebase/ai 3.0.0). Run against the
// project on 16 October 2026 with the Gemini Developer API (which then refused for billing); the
// Agent Platform backend has not been run against Google from the build environment.

import type { Content, FunctionDeclaration, ObjectSchemaRequest, Part, SchemaRequest } from "firebase/ai";
import { GeminiProvider, MODEL_CHAIN, OfflineProvider, type AIProvider, type AiPart, type ChatCall, type ChatPart, type ChatTransport, type ChatTurn, type ModelCall, type Transport } from "@/lib/ai";
import { firebaseEnabled, getFirebaseApp } from "@/lib/firebase";

/** Gemini 3 models on Agent Platform are served from the global endpoint. */
export const AI_LOCATION = "global";

const toPart = (part: AiPart): Part => ("text" in part ? { type: "text", text: part.text } : { type: "inlineData", inlineData: { mimeType: part.file.mimeType, data: part.file.data } });

export const firebaseTransport: Transport = async (call: ModelCall): Promise<string> => {
  const [app, { getAI, getGenerativeModel, AgentPlatformBackend }] = await Promise.all([getFirebaseApp(), import("firebase/ai")]);
  const ai = getAI(app, { backend: new AgentPlatformBackend(AI_LOCATION) });
  const model = getGenerativeModel(ai, {
    model: call.model,
    systemInstruction: call.system,
    // No temperature or penalties: Gemini 3 models ignore the first and reject the second.
    // The schemas (lib/engine/reading.ts) are written in the OpenAPI form responseSchema takes
    // ("nullable", "enum"), not as JSON Schema, so they go in responseSchema.
    generationConfig: call.jsonSchema ? { responseMimeType: "application/json", responseSchema: call.jsonSchema as unknown as SchemaRequest } : undefined,
  });
  const result = await model.generateContent({ contents: [{ role: "user", parts: call.parts.map(toPart) }] }, { signal: call.signal });
  // text() throws an AIError (response-error) when the answer was blocked.
  return result.response.text();
};

const toChatPart = (part: ChatPart): Part =>
  "text" in part
    ? { type: "text", text: part.text }
    : "functionCall" in part
      ? { type: "functionCall", functionCall: { name: part.functionCall.name, args: part.functionCall.args, id: part.functionCall.id } }
      : { type: "functionResponse", functionResponse: { name: part.functionResponse.name, response: part.functionResponse.response, id: part.functionResponse.id } };

/**
 * Function results go back with the "user" role: the SDK itself does so for Gemini 3.6 and later
 * (assignRoleToPartsAndValidateSendMessageRequest in @firebase/ai 3.0.0).
 */
const toContent = (turn: ChatTurn): Content => ({ role: turn.role === "model" ? "model" : "user", parts: turn.parts.map(toChatPart) });

/** NOT RUN AGAINST GOOGLE YET (see the top of this file). Follows the firebase 13.0.0 types. */
export const firebaseChatTransport: ChatTransport = async (call: ChatCall): Promise<ChatTurn> => {
  const [app, { getAI, getGenerativeModel, AgentPlatformBackend }] = await Promise.all([getFirebaseApp(), import("firebase/ai")]);
  const ai = getAI(app, { backend: new AgentPlatformBackend(AI_LOCATION) });
  const functionDeclarations: FunctionDeclaration[] = call.tools.map((tool) => ({ name: tool.name, description: tool.description, parameters: tool.parameters as unknown as ObjectSchemaRequest }));
  const model = getGenerativeModel(ai, { model: call.model, systemInstruction: call.system, tools: functionDeclarations.length ? [{ functionDeclarations }] : undefined });
  const result = await model.generateContent({ contents: call.history.map(toContent) }, { signal: call.signal });
  const calls = result.response.functionCalls() ?? [];
  if (calls.length) return { role: "model", parts: calls.map((c) => ({ functionCall: { name: c.name, args: (c.args ?? {}) as Record<string, unknown>, id: c.id } })) };
  return { role: "model", parts: [{ text: result.response.text() }] };
};

let provider: AIProvider | null = null;

/** The provider for this copy of the app: Gemini when Firebase is configured, otherwise offline. */
export function aiProvider(): AIProvider {
  provider ??= firebaseEnabled ? new GeminiProvider(firebaseTransport, MODEL_CHAIN, Date.now, firebaseChatTransport) : new OfflineProvider();
  return provider;
}
