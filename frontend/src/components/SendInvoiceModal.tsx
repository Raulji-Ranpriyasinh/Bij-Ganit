import React, { useState } from "react";

interface SendInvoiceModalProps {
  isOpen: boolean;
  onClose: () => void;
  invoiceId: number;
  invoiceNumber?: string;
  customerEmail?: string;
  onSendSuccess?: () => void;
}

export const SendInvoiceModal: React.FC<SendInvoiceModalProps> = ({
  isOpen,
  onClose,
  invoiceId,
  invoiceNumber,
  customerEmail,
  onSendSuccess,
}) => {
  const [activeTab, setActiveTab] = useState<"compose" | "preview">("compose");
  const [to, setTo] = useState(customerEmail || "");
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [attachPdf, setAttachPdf] = useState(true);
  const [loading, setLoading] = useState(false);
  const [previewData, setPreviewData] = useState<{ subject: string; body: string } | null>(null);

  // Load preview when opening modal or switching to preview tab
  React.useEffect(() => {
    if (isOpen && activeTab === "preview") {
      loadPreview();
    }
  }, [isOpen, activeTab]);

  const loadPreview = async () => {
    try {
      const { invoicePdfApi } = await import("../api/pdf");
      const response = await invoicePdfApi.previewInvoiceEmail(invoiceId);
      setPreviewData({ subject: response.subject, body: response.body });
      if (!subject) setSubject(response.subject);
      if (!body) setBody(response.body);
    } catch (error) {
      console.error("Failed to load email preview:", error);
    }
  };

  const handleSend = async () => {
    if (!to) {
      alert("Please enter recipient email address");
      return;
    }

    setLoading(true);
    try {
      const { invoicePdfApi } = await import("../api/pdf");
      await invoicePdfApi.sendInvoice(invoiceId, {
        to,
        subject: subject || previewData?.subject || "",
        body: body || previewData?.body || "",
        attach_pdf: attachPdf,
      });
      onSendSuccess?.();
      onClose();
    } catch (error: any) {
      alert(`Failed to send email: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl mx-4">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b">
          <h2 className="text-lg font-semibold">
            Send Invoice {invoiceNumber ? `#${invoiceNumber}` : ""}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl"
          >
            ×
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b">
          <button
            className={`px-4 py-2 ${activeTab === "compose" ? "border-b-2 border-purple-600 text-purple-600" : "text-gray-600"}`}
            onClick={() => setActiveTab("compose")}
          >
            Compose
          </button>
          <button
            className={`px-4 py-2 ${activeTab === "preview" ? "border-b-2 border-purple-600 text-purple-600" : "text-gray-600"}`}
            onClick={() => setActiveTab("preview")}
          >
            Preview
          </button>
        </div>

        {/* Content */}
        <div className="p-4 space-y-4">
          {activeTab === "compose" ? (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  To
                </label>
                <input
                  type="email"
                  value={to}
                  onChange={(e) => setTo(e.target.value)}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500"
                  placeholder="customer@example.com"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Subject
                </label>
                <input
                  type="text"
                  value={subject}
                  onChange={(e) => setSubject(e.target.value)}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500"
                  placeholder="Invoice #INV-001"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Message
                </label>
                <textarea
                  value={body}
                  onChange={(e) => setBody(e.target.value)}
                  rows={8}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500"
                  placeholder="Enter your message here..."
                />
              </div>

              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="attachPdf"
                  checked={attachPdf}
                  onChange={(e) => setAttachPdf(e.target.checked)}
                  className="mr-2"
                />
                <label htmlFor="attachPdf" className="text-sm text-gray-700">
                  Attach PDF invoice
                </label>
              </div>
            </>
          ) : (
            <div className="space-y-4">
              {previewData ? (
                <>
                  <div>
                    <strong className="text-gray-700">Subject:</strong>
                    <p className="mt-1 text-gray-600">{previewData.subject}</p>
                  </div>
                  <div>
                    <strong className="text-gray-700">Preview:</strong>
                    <div
                      className="mt-2 p-4 border rounded-md bg-gray-50"
                      dangerouslySetInnerHTML={{ __html: previewData.body }}
                    />
                  </div>
                </>
              ) : (
                <p className="text-gray-500">Loading preview...</p>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex justify-end gap-3 p-4 border-t bg-gray-50 rounded-b-lg">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-md"
          >
            Cancel
          </button>
          <button
            onClick={handleSend}
            disabled={loading}
            className="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:opacity-50"
          >
            {loading ? "Sending..." : "Send Invoice"}
          </button>
        </div>
      </div>
    </div>
  );
};
