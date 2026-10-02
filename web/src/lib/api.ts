import type { z } from "zod";

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
  }
}

async function failure(response: Response): Promise<ApiError> {
  let detail = "";
  try {
    const body: unknown = await response.json();
    if (
      typeof body === "object" &&
      body &&
      "detail" in body &&
      typeof body.detail === "string"
    )
      detail = body.detail;
  } catch {
    // not JSON: the status is explanation enough
  }
  return new ApiError(detail || `Error ${response.status}`, response.status);
}

async function send(
  path: string,
  method: string,
  body?: unknown,
): Promise<Response> {
  let response: Response;
  try {
    response = await fetch(`/api${path}`, {
      method,
      headers:
        body === undefined ? undefined : { "Content-Type": "application/json" },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch {
    throw new ApiError("No se pudo conectar con el servidor de carrera.", 0);
  }
  if (!response.ok) throw await failure(response);
  return response;
}

/** Every response is validated: a server change shows up here, not as a blank screen. */
export async function request<S extends z.ZodType>(
  schema: S,
  path: string,
  method = "GET",
  body?: unknown,
): Promise<z.infer<S>> {
  return schema.parse(await (await send(path, method, body)).json());
}

export async function requestPdf(path: string, body?: unknown): Promise<Blob> {
  return (await send(path, body === undefined ? "GET" : "POST", body)).blob();
}

export async function command(
  path: string,
  method = "POST",
  body?: unknown,
): Promise<void> {
  await send(path, method, body);
}
