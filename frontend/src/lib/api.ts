const API_URL = "/api/backend";

// ============================================================
// Types
// ============================================================

export interface Document {
  document_id: string;
  filename: string;
  page_count: number;
  chunk_count: number;
}

export interface DocumentsResponse {
  count: number;
  documents: Document[];
}

export interface UploadResponse {
  status: string;
  message: string;
  document_id: string;
  filename: string;
  stored_filename: string;
}

export interface DocumentStatus {
  status:
    | "queued"
    | "processing"
    | "completed"
    | "failed";

  document_id: string;

  filename: string;

  user_id?: string;

  page_count?: number;

  chunk_count?: number;

  embedding_dimension?: number;

  error?: string;
}

export interface Source {
  document_id?: string;
  filename: string;
  page: number;
  chunk: number;
  reranker_score: number;
}

export interface AskResponse {
  question: string;
  document_id?: string | null;
  answer: string;
  sources: Source[];
}

export interface DeleteResponse {
  status: string;
  message: string;
  document_id: string;
  filename?: string;
  deleted_chunks: number;
  deleted_file: boolean;
}


// ============================================================
// Get Documents
// ============================================================

export async function getDocuments(): Promise<Document[]> {
  const response = await fetch(
    `${API_URL}/documents`,
    {
      method: "GET",
      cache: "no-store",
    }
  );

  if (!response.ok) {
    const error =
      await response
        .json()
        .catch(() => null);

    throw new Error(
      error?.detail ||
        "Failed to load documents."
    );
  }

  const data: DocumentsResponse =
    await response.json();

  return data.documents;
}


// ============================================================
// Upload Document
// ============================================================

export async function uploadDocument(
  file: File
): Promise<UploadResponse> {

  const formData = new FormData();

  formData.append(
    "file",
    file
  );

  const response = await fetch(
    `${API_URL}/documents/upload`,
    {
      method: "POST",
      body: formData,
    }
  );

  if (!response.ok) {

    const error =
      await response
        .json()
        .catch(() => null);

    throw new Error(
      error?.detail ||
        "Failed to upload document."
    );
  }

  return response.json();
}


// ============================================================
// Get Document Status
// ============================================================

export async function getDocumentStatus(
  documentId: string
): Promise<DocumentStatus> {

  const response = await fetch(
    `${API_URL}/documents/${documentId}/status`,
    {
      method: "GET",
      cache: "no-store",
    }
  );

  if (!response.ok) {

    const error =
      await response
        .json()
        .catch(() => null);

    throw new Error(
      error?.detail ||
        "Failed to get document status."
    );
  }

  return response.json();
}


// ============================================================
// Ask Question
// ============================================================

export async function askQuestion(
  question: string,
  documentId?: string
): Promise<AskResponse> {

  const response = await fetch(
    `${API_URL}/ask`,
    {
      method: "POST",

      headers: {
        "Content-Type":
          "application/json",
      },

      body: JSON.stringify({
        question,

        document_id:
          documentId || null,
      }),
    }
  );

  if (!response.ok) {

    const error =
      await response
        .json()
        .catch(() => null);

    throw new Error(
      error?.detail ||
        "Failed to get answer."
    );
  }

  return response.json();
}


// ============================================================
// Delete Document
// ============================================================

export async function deleteDocument(
  documentId: string
): Promise<DeleteResponse> {

  const response = await fetch(
    `${API_URL}/documents/${documentId}`,
    {
      method: "DELETE",
    }
  );

  if (!response.ok) {

    const error =
      await response
        .json()
        .catch(() => null);

    throw new Error(
      error?.detail ||
        "Failed to delete document."
    );
  }

  return response.json();
}