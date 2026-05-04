import React, { useState } from "react";

interface MailConfig {
  driver: "smtp" | "mailgun" | "ses" | "sendmail";
  mail_from: string;
  smtp_host?: string;
  smtp_port?: number;
  smtp_user?: string;
  smtp_password?: string;
  smtp_tls?: boolean;
  mailgun_api_key?: string;
  mailgun_domain?: string;
  ses_access_key?: string;
  ses_secret_key?: string;
  ses_region?: string;
}

const driverFields: Record<string, (keyof MailConfig)[]> = {
  smtp: ["mail_from", "smtp_host", "smtp_port", "smtp_user", "smtp_password", "smtp_tls"],
  mailgun: ["mail_from", "mailgun_api_key", "mailgun_domain"],
  ses: ["mail_from", "ses_access_key", "ses_secret_key", "ses_region"],
  sendmail: ["mail_from"],
};

export const MailConfigurationPage: React.FC = () => {
  const [config, setConfig] = useState<MailConfig>({
    driver: "smtp",
    mail_from: "",
    smtp_host: "smtp.gmail.com",
    smtp_port: 587,
    smtp_user: "",
    smtp_password: "",
    smtp_tls: true,
    mailgun_api_key: "",
    mailgun_domain: "",
    ses_access_key: "",
    ses_secret_key: "",
    ses_region: "us-east-1",
  });

  const [testing, setTesting] = useState(false);
  const [testEmail, setTestEmail] = useState("");
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const handleChange = (field: keyof MailConfig, value: any) => {
    setConfig((prev) => ({ ...prev, [field]: value }));
  };

  const handleSave = async () => {
    try {
      // TODO: Implement save to backend
      setMessage({ type: "success", text: "Mail configuration saved successfully!" });
    } catch (error: any) {
      setMessage({ type: "error", text: `Failed to save: ${error.message}` });
    }
  };

  const handleTestEmail = async () => {
    if (!testEmail) {
      setMessage({ type: "error", text: "Please enter a test email address" });
      return;
    }

    setTesting(true);
    try {
      // TODO: Implement test email endpoint
      await new Promise((resolve) => setTimeout(resolve, 1000)); // Simulated delay
      setMessage({ type: "success", text: `Test email sent to ${testEmail}!` });
    } catch (error: any) {
      setMessage({ type: "error", text: `Failed to send test email: ${error.message}` });
    } finally {
      setTesting(false);
    }
  };

  const currentFields = driverFields[config.driver];

  return (
    <div className="max-w-3xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6">Mail Configuration</h1>

      {message && (
        <div
          className={`mb-4 p-4 rounded-md ${
            message.type === "success" ? "bg-green-50 text-green-800" : "bg-red-50 text-red-800"
          }`}
        >
          {message.text}
        </div>
      )}

      <div className="bg-white shadow rounded-lg p-6 space-y-6">
        {/* Driver Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Email Driver
          </label>
          <select
            value={config.driver}
            onChange={(e) => handleChange("driver", e.target.value)}
            className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500"
          >
            <option value="smtp">SMTP</option>
            <option value="mailgun">Mailgun</option>
            <option value="ses">Amazon SES</option>
            <option value="sendmail">Sendmail</option>
          </select>
        </div>

        {/* Dynamic Fields Based on Driver */}
        {currentFields.includes("mail_from") && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              From Email
            </label>
            <input
              type="email"
              value={config.mail_from}
              onChange={(e) => handleChange("mail_from", e.target.value)}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500"
              placeholder="noreply@example.com"
            />
          </div>
        )}

        {currentFields.includes("smtp_host") && (
          <>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                SMTP Host
              </label>
              <input
                type="text"
                value={config.smtp_host}
                onChange={(e) => handleChange("smtp_host", e.target.value)}
                className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500"
                placeholder="smtp.gmail.com"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                SMTP Port
              </label>
              <input
                type="number"
                value={config.smtp_port}
                onChange={(e) => handleChange("smtp_port", parseInt(e.target.value))}
                className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500"
                placeholder="587"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                SMTP Username
              </label>
              <input
                type="text"
                value={config.smtp_user}
                onChange={(e) => handleChange("smtp_user", e.target.value)}
                className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500"
                placeholder=""
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                SMTP Password
              </label>
              <input
                type="password"
                value={config.smtp_password}
                onChange={(e) => handleChange("smtp_password", e.target.value)}
                className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500"
                placeholder=""
              />
            </div>

            <div className="flex items-center">
              <input
                type="checkbox"
                id="smtp_tls"
                checked={config.smtp_tls}
                onChange={(e) => handleChange("smtp_tls", e.target.checked)}
                className="mr-2"
              />
              <label htmlFor="smtp_tls" className="text-sm text-gray-700">
                Use TLS/STARTTLS
              </label>
            </div>
          </>
        )}

        {currentFields.includes("mailgun_api_key") && (
          <>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Mailgun API Key
              </label>
              <input
                type="password"
                value={config.mailgun_api_key}
                onChange={(e) => handleChange("mailgun_api_key", e.target.value)}
                className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500"
                placeholder=""
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Mailgun Domain
              </label>
              <input
                type="text"
                value={config.mailgun_domain}
                onChange={(e) => handleChange("mailgun_domain", e.target.value)}
                className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500"
                placeholder="mg.example.com"
              />
            </div>
          </>
        )}

        {currentFields.includes("ses_access_key") && (
          <>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                AWS Access Key
              </label>
              <input
                type="password"
                value={config.ses_access_key}
                onChange={(e) => handleChange("ses_access_key", e.target.value)}
                className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500"
                placeholder=""
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                AWS Secret Key
              </label>
              <input
                type="password"
                value={config.ses_secret_key}
                onChange={(e) => handleChange("ses_secret_key", e.target.value)}
                className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500"
                placeholder=""
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                AWS Region
              </label>
              <input
                type="text"
                value={config.ses_region}
                onChange={(e) => handleChange("ses_region", e.target.value)}
                className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500"
                placeholder="us-east-1"
              />
            </div>
          </>
        )}

        {/* Test Email Section */}
        <div className="pt-4 border-t">
          <h3 className="text-lg font-medium mb-3">Test Email Configuration</h3>
          <div className="flex gap-3">
            <input
              type="email"
              value={testEmail}
              onChange={(e) => setTestEmail(e.target.value)}
              className="flex-1 border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500"
              placeholder="Enter email address for testing"
            />
            <button
              onClick={handleTestEmail}
              disabled={testing}
              className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 disabled:opacity-50"
            >
              {testing ? "Sending..." : "Send Test Email"}
            </button>
          </div>
        </div>

        {/* Save Button */}
        <div className="pt-4 border-t flex justify-end">
          <button
            onClick={handleSave}
            className="px-6 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700"
          >
            Save Configuration
          </button>
        </div>
      </div>
    </div>
  );
};
