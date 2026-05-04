import { api } from "./client";

export interface SendEmailRequest {
  to: string | string[];
  subject: string;
  body: string;
  attach_pdf?: boolean;
}

export interface EmailPreview {
  subject: string;
  body: string;
  placeholders: Record<string, string>;
}

export interface TemplateInfo {
  name: string;
  display_name: string;
  preview_url: string;
  path: string;
}

// Invoice PDF & Email endpoints
export const invoicePdfApi = {
  // Get PDF or HTML preview
  getInvoicePdf: async (invoiceId: number, preview = false): Promise<Blob | string> => {
    const response = await api.get(`/v1/invoices/${invoiceId}/pdf`, {
      params: { preview },
      responseType: preview ? "text" : "blob",
    });
    return response.data;
  },

  // Download PDF
  downloadInvoicePdf: async (invoiceId: number): Promise<void> => {
    const response = await api.get(`/v1/invoices/${invoiceId}/pdf`, {
      responseType: "blob",
    });
    
    // Create blob and trigger download
    const blob = new Blob([response.data], { type: "application/pdf" });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `Invoice-${invoiceId}.pdf`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  },

  // List available templates
  getTemplates: async (): Promise<TemplateInfo[]> => {
    const response = await api.get("/v1/invoices/templates");
    return response.data.templates;
  },

  // Send invoice via email
  sendInvoice: async (invoiceId: number, data: SendEmailRequest): Promise<any> => {
    const response = await api.post(`/v1/invoices/${invoiceId}/send`, data);
    return response.data;
  },

  // Preview email content
  previewInvoiceEmail: async (invoiceId: number): Promise<EmailPreview> => {
    const response = await api.get(`/v1/invoices/${invoiceId}/send/preview`);
    return response.data;
  },
};

// Estimate PDF & Email endpoints
export const estimatePdfApi = {
  getEstimatePdf: async (estimateId: number, preview = false): Promise<Blob | string> => {
    const response = await api.get(`/v1/estimates/${estimateId}/pdf`, {
      params: { preview },
      responseType: preview ? "text" : "blob",
    });
    return response.data;
  },

  downloadEstimatePdf: async (estimateId: number): Promise<void> => {
    const response = await api.get(`/v1/estimates/${estimateId}/pdf`, {
      responseType: "blob",
    });
    
    const blob = new Blob([response.data], { type: "application/pdf" });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `Estimate-${estimateId}.pdf`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  },

  getTemplates: async (): Promise<TemplateInfo[]> => {
    const response = await api.get("/v1/estimates/templates");
    return response.data.templates;
  },

  sendEstimate: async (estimateId: number, data: SendEmailRequest): Promise<any> => {
    const response = await api.post(`/v1/estimates/${estimateId}/send`, data);
    return response.data;
  },

  previewEstimateEmail: async (estimateId: number): Promise<EmailPreview> => {
    const response = await api.get(`/v1/estimates/${estimateId}/send/preview`);
    return response.data;
  },
};

// Payment PDF & Email endpoints
export const paymentPdfApi = {
  getPaymentPdf: async (paymentId: number, preview = false): Promise<Blob | string> => {
    const response = await api.get(`/v1/payments/${paymentId}/pdf`, {
      params: { preview },
      responseType: preview ? "text" : "blob",
    });
    return response.data;
  },

  downloadPaymentPdf: async (paymentId: number): Promise<void> => {
    const response = await api.get(`/v1/payments/${paymentId}/pdf`, {
      responseType: "blob",
    });
    
    const blob = new Blob([response.data], { type: "application/pdf" });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `Payment-${paymentId}.pdf`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  },

  getTemplates: async (): Promise<TemplateInfo[]> => {
    const response = await api.get("/v1/payments/templates");
    return response.data.templates;
  },

  sendPayment: async (paymentId: number, data: SendEmailRequest): Promise<any> => {
    const response = await api.post(`/v1/payments/${paymentId}/send`, data);
    return response.data;
  },

  previewPaymentEmail: async (paymentId: number): Promise<EmailPreview> => {
    const response = await api.get(`/v1/payments/${paymentId}/send/preview`);
    return response.data;
  },
};

// Public PDF access (no auth required)
export const publicPdfApi = {
  getPublicPdfUrl: (token: string): string => {
    return `/api/v1/pdf/${token}`;
  },
};
