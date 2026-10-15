// Carries one model call over Firebase AI Logic, with the Gemini Developer API as the backend.
// Loaded only when a screen first asks the AI for something, so the SDK is not in the first download.
//
// NOT RUN AGAINST GOOGLE YET: the build environment could not reach any Google host. The calls
// below follow the type definitions of firebase 13.0.0 (@firebase/ai 3.0.0). First thing to test
// with a real project: a text call, a JSON call with a photo, and what a quota error looks like.

import type { Content, FunctionDeclaration, ObjectSchemaRequest, Part } from "firebase/ai";
import { GeminiProvider, MODEL_CHAIN, OfflineProvider, type AIProvider, type AiPart, type ChatCall, type ChatPart, type ChatTransport, type ChatTurn, type ModelCall, type Transport } from "@/lib/ai";
import { firebaseEnabled, getFirebaseApp } from "@/lib/firebase";

const toPart = (part: AiPart): Part => ("text" in part ? { type: "text", text: part.text } : { type: "inlineData", inlineData: { mimeType: part.file.mimeType, data: part.file.data } });

export const firebaseTransport: Transport = async (call: ModelCall): Promise<string> => {
  const [app, { getAI, getGenerativeModel, GoogleAIBackend }] = await Promise.all([getFirebaseApp(), import("firebase/ai")]);
  const ai = getAI(app, { backend: new GoogleAIBackend() });
  const model = getGenerativeModel(ai, {
    model: call.model,
    systemInstruction: call.system,
    // No temperature or penalties: Gemini 3 models ignore the first and reject the second.
    generationConfig: call.jsonSchema ? { responseMimeType: "application/json", responseJsonSchema: call.jsonSchema } : undefined,
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
  const [app, { getAI, getGenerativeModel, GoogleAIBackend }] = await Promise.all([getFirebaseApp(), import("firebase/ai")]);
  const ai = getAI(app, { backend: new GoogleAIBackend() });
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
