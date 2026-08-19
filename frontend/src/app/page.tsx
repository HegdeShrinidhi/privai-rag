"use client";

import {
  useEffect,
  useState,
} from "react";

import { useSession } from "next-auth/react";

import {
  getDocuments,
  getDocumentStatus,
  uploadDocument,
  deleteDocument,
  Document,
} from "@/lib/api";

import LogoutButton from "@/components/LogoutButton";

export default function Home() {
  // ==========================================================
  // Logged-in user
  // ==========================================================

  const { data: session } = useSession();

  const userName =
    session?.user?.name || "User";

  const userEmail =
    session?.user?.email || "";

  const userInitial =
    userName.charAt(0).toUpperCase();

  // ==========================================================
  // State
  // ==========================================================

  const [documents, setDocuments] =
    useState<Document[]>([]);

  const [loading, setLoading] =
    useState(true);

  const [uploading, setUploading] =
    useState(false);

  const [deletingId, setDeletingId] =
    useState<string | null>(null);

  const [uploadMessage, setUploadMessage] =
    useState("");

  const [error, setError] =
    useState("");

  // ==========================================================
  // Load documents
  // ==========================================================

  async function loadDocuments() {
    try {
      setLoading(true);
      setError("");

      const data = await getDocuments();

      setDocuments(data);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to load documents."
      );
    } finally {
      setLoading(false);
    }
  }

  // ==========================================================
  // Initial load
  // ==========================================================

  useEffect(() => {
    loadDocuments();
  }, []);

  // ==========================================================
  // Upload document
  // ==========================================================

  async function handleUpload(
    event: React.ChangeEvent<HTMLInputElement>
  ) {
    const file =
      event.target.files?.[0];

    if (!file) {
      return;
    }

    if (file.type !== "application/pdf") {
      setError(
        "Only PDF files are supported."
      );

      event.target.value = "";

      return;
    }

    try {
      setUploading(true);
      setError("");

      setUploadMessage(
        "Uploading document..."
      );

      const result =
        await uploadDocument(file);

      const documentId =
        result.document_id;

      setUploadMessage(
        "Document uploaded. Indexing started..."
      );

      // ------------------------------------------------------
      // Poll document processing status
      // ------------------------------------------------------

      let completed = false;
      let attempts = 0;

      const maxAttempts = 120;

      while (
        !completed &&
        attempts < maxAttempts
      ) {
        attempts++;

        await new Promise(
          (resolve) =>
            setTimeout(resolve, 2000)
        );

        const status =
          await getDocumentStatus(
            documentId
          );

        if (
          status.status ===
          "processing"
        ) {
          setUploadMessage(
            "Processing document..."
          );
        }

        if (
          status.status ===
          "completed"
        ) {
          completed = true;

          setUploadMessage(
            "Document indexed successfully."
          );

          await loadDocuments();

          break;
        }

        if (
          status.status ===
          "failed"
        ) {
          throw new Error(
            status.error ||
              "Document processing failed."
          );
        }
      }

      if (!completed) {
        throw new Error(
          "Document processing is taking longer than expected."
        );
      }

      setTimeout(() => {
        setUploadMessage("");
      }, 3000);

    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Upload failed."
      );
    } finally {
      setUploading(false);

      event.target.value = "";
    }
  }

  // ==========================================================
  // Delete document
  // ==========================================================

  async function handleDelete(
    documentId: string,
    filename: string
  ) {
    const confirmed =
      window.confirm(
        `Delete "${filename}"?\n\n` +
        `This will permanently remove the PDF ` +
        `and all of its indexed data.`
      );

    if (!confirmed) {
      return;
    }

    try {
      setDeletingId(documentId);
      setError("");

      await deleteDocument(
        documentId
      );

      setDocuments(
        (previous) =>
          previous.filter(
            (document) =>
              document.document_id !==
              documentId
          )
      );

      setUploadMessage(
        `"${filename}" deleted successfully.`
      );

      setTimeout(() => {
        setUploadMessage("");
      }, 3000);

    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to delete document."
      );
    } finally {
      setDeletingId(null);
    }
  }

  // ==========================================================
  // UI
  // ==========================================================

  return (
    <main className="min-h-screen bg-[#080C1C] text-[#F5F7FF]">

      {/* ==================================================== */}
      {/* Header */}
      {/* ==================================================== */}

      <header className="border-b border-[#252B45] bg-[#080C1C]/90 backdrop-blur-xl">

        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-5">

          {/* Logo */}

          <div className="flex items-center gap-3">

            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#5546E8] shadow-lg shadow-[#5546E8]/20">
              ✦
            </div>

            <div>
              <h1 className="text-lg font-semibold">
                PrivAI-RAG
              </h1>

              <p className="text-xs text-[#69728D]">
                Enterprise Document Intelligence
              </p>
            </div>

          </div>

          {/* Right side */}

          <div className="flex items-center gap-4">

            {/* Logged-in user */}

            <div className="hidden items-center gap-3 sm:flex">

              {/* Avatar */}

              <div className="flex h-9 w-9 items-center justify-center rounded-full bg-[#5546E8] text-sm font-semibold text-white shadow-lg shadow-[#5546E8]/20">

                {userInitial}

              </div>

              {/* User information */}

              <div className="leading-tight">

                <p className="max-w-[180px] truncate text-sm font-medium text-[#F5F7FF]">
                  {userName}
                </p>

                <p className="max-w-[220px] truncate text-xs text-[#69728D]">
                  {userEmail}
                </p>

              </div>

            </div>

            {/* Logout */}

            <LogoutButton />

          </div>

        </div>

      </header>

      {/* ==================================================== */}
      {/* Hero */}
      {/* ==================================================== */}

      <section className="relative overflow-hidden">

        <div className="pointer-events-none absolute left-1/2 top-0 h-[500px] w-[700px] -translate-x-1/2 rounded-full bg-[#5546E8]/10 blur-[120px]" />

        <div className="relative mx-auto max-w-7xl px-6 pb-16 pt-20">

          <div className="max-w-4xl">

            {/* Welcome message */}

            <div className="mb-6 flex items-center gap-3">

              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-[#5546E8]/20 text-sm font-semibold text-[#8B87FF]">
                {userInitial}
              </div>

              <p className="text-sm text-[#A7AEC4]">

                Welcome back,{" "}

                <span className="font-semibold text-[#F5F7FF]">
                  {userName}
                </span>

              </p>

            </div>

            {/* Badge */}

            <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-[#5546E8]/30 bg-[#5546E8]/10 px-4 py-2 text-xs font-medium text-[#8B87FF]">

              ✦ PRIVATE AI DOCUMENT INTELLIGENCE

            </div>

            {/* Heading */}

            <h2 className="text-5xl font-bold leading-[1.05] tracking-tight md:text-6xl">

              Your documents,

              <br />

              <span className="gradient-text">
                understood by AI.
              </span>

            </h2>

            <p className="mt-6 max-w-2xl text-lg leading-8 text-[#A7AEC4]">

              Upload enterprise documents and ask
              questions using grounded AI with
              source citations.

            </p>

            {/* Buttons */}

            <div className="mt-8 flex flex-wrap gap-4">

              <label
                className={`
                  cursor-pointer
                  rounded-xl
                  bg-[#5546E8]
                  px-6
                  py-3.5
                  font-medium
                  text-white
                  shadow-lg
                  shadow-[#5546E8]/20
                  transition
                  hover:bg-[#6C63FF]
                  ${
                    uploading
                      ? "pointer-events-none opacity-60"
                      : ""
                  }
                `}
              >

                {uploading
                  ? "Processing..."
                  : "+ Upload PDF"}

                <input
                  type="file"
                  accept=".pdf"
                  className="hidden"
                  disabled={uploading}
                  onChange={
                    handleUpload
                  }
                />

              </label>

              <button
                onClick={() => {
                  document
                    .getElementById(
                      "documents"
                    )
                    ?.scrollIntoView({
                      behavior: "smooth",
                    });
                }}
                className="rounded-xl border border-[#252B45] bg-[#11172D] px-6 py-3.5 font-medium transition hover:border-[#5546E8]/60"
              >
                Explore Documents →
              </button>

            </div>

            {/* Upload status */}

            {uploadMessage && (
              <div className="mt-5 flex items-center gap-3 text-sm text-[#A7AEC4]">

                <span className="h-2 w-2 animate-pulse rounded-full bg-[#6C63FF]" />

                {uploadMessage}

              </div>
            )}

            {/* Error */}

            {error && (
              <div className="mt-5 rounded-xl border border-red-500/20 bg-red-500/5 p-4 text-sm text-red-400">

                {error}

              </div>
            )}

          </div>

        </div>

      </section>

      {/* ==================================================== */}
      {/* Documents */}
      {/* ==================================================== */}

      <section
        id="documents"
        className="border-t border-[#252B45]"
      >

        <div className="mx-auto max-w-7xl px-6 py-16">

          {/* Section heading */}

          <div className="mb-8 flex items-end justify-between">

            <div>

              <p className="text-sm font-medium text-[#6C63FF]">
                DOCUMENT LIBRARY
              </p>

              <h3 className="mt-2 text-3xl font-bold">
                Your Documents
              </h3>

              <p className="mt-2 text-[#69728D]">
                Documents indexed and ready for
                intelligent search.
              </p>

            </div>

            <button
              onClick={loadDocuments}
              disabled={
                loading ||
                deletingId !== null
              }
              className="rounded-lg border border-[#252B45] bg-[#11172D] px-4 py-2 text-sm text-[#A7AEC4] transition hover:border-[#5546E8]/50 disabled:cursor-not-allowed disabled:opacity-50"
            >

              {loading
                ? "Loading..."
                : "↻ Refresh"}

            </button>

          </div>

          {/* Loading */}

          {loading && (
            <div className="rounded-2xl border border-[#252B45] bg-[#11172D] p-12 text-center">

              <div className="mx-auto mb-4 h-8 w-8 animate-spin rounded-full border-2 border-[#252B45] border-t-[#6C63FF]" />

              <p className="text-sm text-[#A7AEC4]">
                Loading documents...
              </p>

            </div>
          )}

          {/* Error */}

          {!loading &&
            error &&
            documents.length === 0 && (
              <div className="rounded-2xl border border-red-500/20 bg-red-500/5 p-8 text-center">

                <p className="text-red-400">
                  {error}
                </p>

              </div>
            )}

          {/* Empty */}

          {!loading &&
            documents.length === 0 &&
            !error && (
              <div className="rounded-2xl border border-dashed border-[#252B45] bg-[#11172D]/50 p-16 text-center">

                <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-[#5546E8]/10 text-2xl">
                  📄
                </div>

                <h4 className="mt-5 text-lg font-semibold">
                  No documents yet
                </h4>

                <p className="mx-auto mt-2 max-w-md text-sm text-[#69728D]">
                  Upload a PDF to create your first
                  searchable knowledge source.
                </p>

              </div>
            )}

          {/* Document cards */}

          {!loading &&
            documents.length > 0 && (

              <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">

                {documents.map(
                  (document) => {

                    const isDeleting =
                      deletingId ===
                      document.document_id;

                    return (
                      <div
                        key={
                          document.document_id
                        }
                        className={`
                          group
                          rounded-2xl
                          border
                          border-[#252B45]
                          bg-[#11172D]
                          p-6
                          transition
                          duration-300
                          hover:-translate-y-1
                          hover:border-[#5546E8]/50
                          hover:shadow-xl
                          hover:shadow-[#5546E8]/5
                          ${
                            isDeleting
                              ? "opacity-60"
                              : ""
                          }
                        `}
                      >

                        {/* Card header */}

                        <div className="flex items-start justify-between">

                          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-[#5546E8]/10 text-xl">
                            📄
                          </div>

                          <span className="flex items-center gap-2 rounded-full bg-[#22C55E]/10 px-3 py-1 text-xs text-[#4ade80]">

                            <span className="h-1.5 w-1.5 rounded-full bg-[#22C55E]" />

                            Indexed

                          </span>

                        </div>

                        {/* Filename */}

                        <h4
                          className="mt-6 truncate font-semibold"
                          title={
                            document.filename
                          }
                        >
                          {document.filename}
                        </h4>

                        {/* Metadata */}

                        <div className="mt-3 flex gap-4 text-sm text-[#69728D]">

                          <span>
                            {document.page_count} pages
                          </span>

                          <span>
                            {document.chunk_count} chunks
                          </span>

                        </div>

                        {/* Actions */}

                        <div className="mt-6 flex gap-3">

                          {/* Chat */}

                          <a
                            href={
                              isDeleting
                                ? undefined
                                : `/chat/${document.document_id}`
                            }
                            onClick={(event) => {
                              if (isDeleting) {
                                event.preventDefault();
                              }
                            }}
                            className={`
                              flex-1
                              rounded-xl
                              border
                              border-[#252B45]
                              bg-[#0D1226]
                              px-4
                              py-3
                              text-center
                              text-sm
                              font-medium
                              transition
                              ${
                                isDeleting
                                  ? "pointer-events-none opacity-50"
                                  : "group-hover:border-[#5546E8]/50 group-hover:bg-[#5546E8]/10"
                              }
                            `}
                          >
                            Chat with document →
                          </a>

                          {/* Delete */}

                          <button
                            type="button"
                            onClick={() =>
                              handleDelete(
                                document.document_id,
                                document.filename
                              )
                            }
                            disabled={
                              isDeleting
                            }
                            title={
                              isDeleting
                                ? "Deleting document..."
                                : "Delete document"
                            }
                            className="
                              flex
                              min-w-[78px]
                              items-center
                              justify-center
                              rounded-xl
                              border
                              border-red-500/20
                              bg-red-500/5
                              px-3
                              py-3
                              text-sm
                              font-medium
                              text-red-400
                              transition
                              hover:border-red-500/40
                              hover:bg-red-500/10
                              disabled:cursor-not-allowed
                              disabled:opacity-50
                            "
                          >

                            {isDeleting ? (
                              <span className="flex items-center gap-2">

                                <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-red-400/30 border-t-red-400" />

                                Deleting

                              </span>
                            ) : (
                              "Delete"
                            )}

                          </button>

                        </div>

                      </div>
                    );
                  }
                )}

              </div>
            )}

        </div>

      </section>

      {/* ==================================================== */}
      {/* Footer */}
      {/* ==================================================== */}

      <footer className="border-t border-[#252B45]">

        <div className="mx-auto flex max-w-7xl flex-col gap-2 px-6 py-8 text-sm text-[#69728D] sm:flex-row sm:items-center sm:justify-between">

          <span>
            PrivAI-RAG
          </span>

          <span>
            Private • Grounded • Enterprise AI
          </span>

        </div>

      </footer>

    </main>
  );
}