"use client";

import {
  useEffect,
  useState,
} from "react";

import {
  askQuestion,
  getDocuments,
  Document,
} from "@/lib/api";

import { useParams } from "next/navigation";


// ============================================================
// Types
// ============================================================

interface Message {
  role: "user" | "assistant";
  content: string;
  sources?: {
    filename: string;
    page: number;
    chunk: number;
    reranker_score: number;
  }[];
}


// ============================================================
// Page
// ============================================================

export default function DocumentChatPage() {

  const params = useParams();

  const documentId =
    params.document_id as string;


  // ==========================================================
  // State
  // ==========================================================

  const [
    document,
    setDocument,
  ] = useState<Document | null>(null);

  const [
    question,
    setQuestion,
  ] = useState("");

  const [
    messages,
    setMessages,
  ] = useState<Message[]>([]);

  const [
    loading,
    setLoading,
  ] = useState(false);

  const [
    pageLoading,
    setPageLoading,
  ] = useState(true);

  const [
    error,
    setError,
  ] = useState("");


  // ==========================================================
  // Load document
  // ==========================================================

  useEffect(() => {

    async function loadDocument() {

      try {

        setPageLoading(true);

        const documents =
          await getDocuments();

        const found =
          documents.find(
            (item) =>
              item.document_id ===
              documentId
          );

        if (!found) {

          setError(
            "Document not found."
          );

          return;
        }

        setDocument(found);

      } catch (err) {

        setError(
          err instanceof Error
            ? err.message
            : "Failed to load document."
        );

      } finally {

        setPageLoading(false);

      }
    }

    if (documentId) {
      loadDocument();
    }

  }, [documentId]);


  // ==========================================================
  // Ask Question
  // ==========================================================

  async function handleAsk() {

    const trimmedQuestion =
      question.trim();

    if (
      !trimmedQuestion ||
      loading
    ) {
      return;
    }


    // --------------------------------------------------------
    // Add user message
    // --------------------------------------------------------

    const userMessage: Message = {
      role: "user",
      content: trimmedQuestion,
    };

    setMessages(
      (previous) => [
        ...previous,
        userMessage,
      ]
    );

    setQuestion("");

    setLoading(true);

    setError("");


    try {

      // ------------------------------------------------------
      // Ask backend
      // ------------------------------------------------------

      const response =
        await askQuestion(
          trimmedQuestion,
          documentId
        );


      // ------------------------------------------------------
      // Add assistant response
      // ------------------------------------------------------

      const assistantMessage:
        Message = {
          role: "assistant",

          content:
            response.answer,

          sources:
            response.sources,
        };


      setMessages(
        (previous) => [
          ...previous,
          assistantMessage,
        ]
      );

    } catch (err) {

      setError(
        err instanceof Error
          ? err.message
          : "Failed to get answer."
      );

    } finally {

      setLoading(false);

    }
  }


  // ==========================================================
  // Enter key
  // ==========================================================

  function handleKeyDown(
    event: React.KeyboardEvent<HTMLTextAreaElement>
  ) {

    if (
      event.key === "Enter" &&
      !event.shiftKey
    ) {

      event.preventDefault();

      handleAsk();
    }
  }


  // ==========================================================
  // Loading
  // ==========================================================

  if (pageLoading) {

    return (

      <main className="flex min-h-screen items-center justify-center bg-[#080C1C] text-white">

        <div className="text-center">

          <div className="mx-auto mb-4 h-8 w-8 animate-spin rounded-full border-2 border-[#252B45] border-t-[#6C63FF]" />

          <p className="text-sm text-[#A7AEC4]">
            Loading document...
          </p>

        </div>

      </main>
    );
  }


  // ==========================================================
  // Document not found
  // ==========================================================

  if (!document) {

    return (

      <main className="min-h-screen bg-[#080C1C] px-6 py-20 text-white">

        <div className="mx-auto max-w-xl rounded-2xl border border-red-500/20 bg-[#11172D] p-10 text-center">

          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-red-500/10 text-2xl">
            !
          </div>

          <h1 className="mt-5 text-2xl font-bold">
            Document not found
          </h1>

          <p className="mt-3 text-[#69728D]">
            {error ||
              "The selected document could not be found."}
          </p>

          <a
            href="/"
            className="mt-6 inline-block rounded-xl bg-[#5546E8] px-5 py-3 text-sm font-medium"
          >
            ← Back to Documents
          </a>

        </div>

      </main>
    );
  }


  // ==========================================================
  // Main Chat UI
  // ==========================================================

  return (

    <main className="flex min-h-screen flex-col bg-[#080C1C] text-[#F5F7FF]">


      {/* ==================================================== */}
      {/* Header */}
      {/* ==================================================== */}

      <header className="border-b border-[#252B45] bg-[#080C1C]/95 backdrop-blur-xl">

        <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-5">

          <div className="flex items-center gap-4">

            <a
              href="/"
              className="flex h-10 w-10 items-center justify-center rounded-xl border border-[#252B45] bg-[#11172D] text-[#A7AEC4] transition hover:border-[#5546E8]/60 hover:text-white"
            >
              ←
            </a>


            <div>

              <p className="text-xs font-medium uppercase tracking-wider text-[#6C63FF]">
                Document Chat
              </p>

              <h1 className="mt-1 max-w-[500px] truncate text-lg font-semibold">
                {document.filename}
              </h1>

            </div>

          </div>


          <div className="hidden items-center gap-3 text-sm text-[#69728D] sm:flex">

            <span>
              {document.page_count} pages
            </span>

            <span>
              •
            </span>

            <span>
              {document.chunk_count} chunks
            </span>

            <span className="flex items-center gap-2 rounded-full bg-[#22C55E]/10 px-3 py-1 text-[#4ade80]">

              <span className="h-1.5 w-1.5 rounded-full bg-[#22C55E]" />

              Indexed

            </span>

          </div>

        </div>

      </header>


      {/* ==================================================== */}
      {/* Chat Area */}
      {/* ==================================================== */}

      <section className="flex-1">

        <div className="mx-auto flex min-h-[calc(100vh-170px)] w-full max-w-4xl flex-col px-6 py-10">


          {/* Empty state */}

          {messages.length === 0 && (

            <div className="flex flex-1 flex-col items-center justify-center text-center">

              <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-[#5546E8]/10 text-3xl">
                ✦
              </div>

              <h2 className="mt-6 text-3xl font-bold">
                Ask this document anything.
              </h2>

              <p className="mt-3 max-w-xl text-[#69728D]">
                Ask questions about{" "}
                <span className="text-[#A7AEC4]">
                  {document.filename}
                </span>
                . Answers are generated only from
                this document.
              </p>


              <div className="mt-8 grid w-full max-w-2xl gap-3 sm:grid-cols-2">

                {[
                  "Give me a summary of this document.",
                  "What are the main skills mentioned?",
                  "What experience is listed?",
                  "What technologies are mentioned?",
                ].map(
                  (suggestion) => (

                    <button
                      key={suggestion}
                      onClick={() =>
                        setQuestion(
                          suggestion
                        )
                      }
                      className="rounded-xl border border-[#252B45] bg-[#11172D] p-4 text-left text-sm text-[#A7AEC4] transition hover:border-[#5546E8]/50 hover:bg-[#5546E8]/5 hover:text-white"
                    >

                      {suggestion}

                    </button>

                  )
                )}

              </div>

            </div>

          )}


          {/* Messages */}

          {messages.length > 0 && (

            <div className="space-y-8">

              {messages.map(
                (message, index) => (

                  <div
                    key={index}
                    className={
                      message.role ===
                      "user"
                        ? "flex justify-end"
                        : "flex justify-start"
                    }
                  >

                    <div
                      className={
                        message.role ===
                        "user"
                          ? "max-w-2xl rounded-2xl rounded-br-md bg-[#5546E8] px-5 py-4"
                          : "max-w-3xl"
                      }
                    >

                      {message.role ===
                      "assistant" && (

                        <div className="mb-3 flex items-center gap-2 text-xs font-medium text-[#6C63FF]">

                          <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-[#5546E8]/10">
                            ✦
                          </span>

                          PrivAI

                        </div>

                      )}


                      <div className="whitespace-pre-wrap text-sm leading-7">

                        {message.content}

                      </div>


                      {/* Sources */}

                      {message.sources &&
                        message.sources.length >
                          0 && (

                          <div className="mt-5 border-t border-[#252B45] pt-4">

                            <p className="mb-3 text-xs font-medium uppercase tracking-wider text-[#69728D]">
                              Sources
                            </p>

                            <div className="space-y-2">

                              {message.sources.map(
                                (
                                  source,
                                  sourceIndex
                                ) => (

                                  <div
                                    key={
                                      sourceIndex
                                    }
                                    className="rounded-lg border border-[#252B45] bg-[#11172D] px-3 py-2 text-xs text-[#69728D]"
                                  >

                                    <span className="text-[#A7AEC4]">
                                      {source.filename}
                                    </span>

                                    {" · "}

                                    Page{" "}
                                    {
                                      source.page
                                    }

                                    {" · "}

                                    Chunk{" "}
                                    {
                                      source.chunk
                                    }

                                  </div>

                                )
                              )}

                            </div>

                          </div>

                        )}

                    </div>

                  </div>

                )
              )}


              {/* Loading */}

              {loading && (

                <div className="flex items-start gap-3">

                  <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-[#5546E8]/10 text-[#6C63FF]">
                    ✦
                  </div>

                  <div className="rounded-xl border border-[#252B45] bg-[#11172D] px-5 py-4">

                    <div className="flex items-center gap-2">

                      <span className="h-2 w-2 animate-bounce rounded-full bg-[#6C63FF]" />

                      <span className="h-2 w-2 animate-bounce rounded-full bg-[#6C63FF] [animation-delay:150ms]" />

                      <span className="h-2 w-2 animate-bounce rounded-full bg-[#6C63FF] [animation-delay:300ms]" />

                    </div>

                  </div>

                </div>

              )}

            </div>

          )}

        </div>

      </section>


      {/* ==================================================== */}
      {/* Error */}
      {/* ==================================================== */}

      {error && messages.length > 0 && (

        <div className="mx-auto mb-4 w-full max-w-4xl px-6">

          <div className="rounded-xl border border-red-500/20 bg-red-500/5 px-4 py-3 text-sm text-red-400">

            {error}

          </div>

        </div>

      )}


      {/* ==================================================== */}
      {/* Input */}
      {/* ==================================================== */}

      <div className="sticky bottom-0 border-t border-[#252B45] bg-[#080C1C]/95 px-6 py-5 backdrop-blur-xl">

        <div className="mx-auto max-w-4xl">

          <div className="flex items-end gap-3 rounded-2xl border border-[#252B45] bg-[#11172D] p-2 transition focus-within:border-[#5546E8]/60">

            <textarea
              value={question}
              onChange={(event) =>
                setQuestion(
                  event.target.value
                )
              }
              onKeyDown={
                handleKeyDown
              }
              placeholder={`Ask a question about ${document.filename}...`}
              rows={1}
              disabled={loading}
              className="max-h-32 min-h-[48px] flex-1 resize-none bg-transparent px-3 py-3 text-sm text-white outline-none placeholder:text-[#69728D]"
            />


            <button
              onClick={
                handleAsk
              }
              disabled={
                loading ||
                !question.trim()
              }
              className="rounded-xl bg-[#5546E8] px-5 py-3 text-sm font-medium text-white transition hover:bg-[#6C63FF] disabled:cursor-not-allowed disabled:opacity-40"
            >

              {loading
                ? "..."
                : "Ask"}

            </button>

          </div>


          <p className="mt-3 text-center text-xs text-[#4F5872]">
            Answers are grounded in the selected document.
          </p>

        </div>

      </div>

    </main>
  );
}