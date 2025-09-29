import { useState, useEffect, useRef } from 'react';
import Head from 'next/head';

export default function Home() {
  const [url, setUrl] = useState('');
  const [prompt, setPrompt] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [saveApiKey, setSaveApiKey] = useState(false);
  const [loading, setLoading] = useState(false);
  const [statusMessages, setStatusMessages] = useState<string[]>([]);
  const [result, setResult] = useState<{
    analysis: string;
    screenshot: string;
  } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const statusEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to latest status message
  useEffect(() => {
    statusEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [statusMessages]);

  // Load saved API key on mount
  useEffect(() => {
    const savedKey = localStorage.getItem('openai_api_key');
    if (savedKey) {
      setApiKey(savedKey);
      setSaveApiKey(true);
    }
  }, []);

  // Save/remove API key when checkbox changes
  const handleSaveApiKeyChange = (checked: boolean) => {
    setSaveApiKey(checked);
    if (checked && apiKey) {
      localStorage.setItem('openai_api_key', apiKey);
    } else {
      localStorage.removeItem('openai_api_key');
    }
  };

  // Update saved key when API key changes and save is enabled
  const handleApiKeyChange = (value: string) => {
    setApiKey(value);
    if (saveApiKey) {
      localStorage.setItem('openai_api_key', value);
    }
  };

  const handleVerify = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!url || !prompt) {
      setError('Please enter both URL and prompt');
      return;
    }

    if (!apiKey) {
      setError('Please enter your OpenAI API key');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);
    setStatusMessages([]);

    try {
      const response = await fetch('/api/verify-stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url, prompt, apiKey }),
      });

      if (!response.ok) {
        throw new Error('Request failed');
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) {
        throw new Error('No response body');
      }

      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = JSON.parse(line.slice(6));

            if (data.type === 'status') {
              setStatusMessages(prev => [...prev, data.message]);
            } else if (data.type === 'error') {
              setError(data.error);
              setLoading(false);
            } else if (data.type === 'complete') {
              setResult({
                analysis: data.analysis,
                screenshot: data.screenshot,
              });
              setLoading(false);
            }
          }
        }
      }
    } catch (err: any) {
      setError(err.message || 'An error occurred');
      setLoading(false);
    }
  };

  return (
    <>
      <Head>
        <title>Vision-Based Page Verification</title>
        <meta name="description" content="AI-powered web page verification tool" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <main className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-5xl mx-auto">
          {/* Header */}
          <div className="text-center mb-12">
            <h1 className="text-4xl font-bold text-gray-900 mb-4">
              AI based analysis of web pages
            </h1>
            <p className="text-lg text-gray-600">
              This tool uses AI to analyze web pages and provide a response to a prompt.
            </p>
          </div>

          {/* Form */}
          <div className="bg-white rounded-lg shadow-xl p-8 mb-8">
            {/* Info Banner */}
            <div className="mb-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex items-start">
                <span className="text-blue-600 text-xl mr-3">🔑</span>
                <div className="text-sm text-blue-800">
                  <p className="font-semibold mb-1">Bring Your Own API Key</p>
                  <p>This is a public tool. You need to provide your own OpenAI API key to use it. 
                  Your key is sent directly to OpenAI and is never stored on our servers. 
                  Get a key at <a href="https://platform.openai.com/api-keys" target="_blank" rel="noopener noreferrer" className="underline font-medium">platform.openai.com/api-keys</a></p>
                </div>
              </div>
            </div>

            <form onSubmit={handleVerify} className="space-y-6">
              <div>
                <label htmlFor="apiKey" className="block text-sm font-medium text-gray-700 mb-2">
                  OpenAI API Key <span className="text-red-500">*</span>
                </label>
                <input
                  type="password"
                  id="apiKey"
                  value={apiKey}
                  onChange={(e) => handleApiKeyChange(e.target.value)}
                  placeholder="sk-..."
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition duration-200 font-mono text-sm"
                  required
                  disabled={loading}
                />
                <div className="mt-2 flex items-center">
                  <input
                    type="checkbox"
                    id="saveApiKey"
                    checked={saveApiKey}
                    onChange={(e) => handleSaveApiKeyChange(e.target.checked)}
                    className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                    disabled={loading}
                  />
                  <label htmlFor="saveApiKey" className="ml-2 text-xs text-gray-600">
                    Remember my API key (stored locally in your browser only)
                  </label>
                </div>
                <p className="mt-1 text-xs text-gray-500">
                  Your API key is sent directly to OpenAI and is never sent to our servers
                </p>
              </div>

              <div>
                <label htmlFor="url" className="block text-sm font-medium text-gray-700 mb-2">
                  Provide the URL of the page you want to analyze
                </label>
                <input
                  type="url"
                  id="url"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  placeholder="https://example.com"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition duration-200"
                  required
                  disabled={loading}
                />
              </div>

              <div>
                <label htmlFor="prompt" className="block text-sm font-medium text-gray-700 mb-2">
                  What is your question about the page?
                </label>
                <textarea
                  id="prompt"
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  placeholder="Example: Check if the page has a contact form and describe its fields..."
                  rows={4}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition duration-200"
                  required
                  disabled={loading}
                />
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-400 text-white font-semibold py-3 px-6 rounded-lg transition duration-200 flex items-center justify-center space-x-2"
              >
                {loading ? (
                  <>
                    <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    <span>Analyzing...</span>
                  </>
                ) : (
                  <span>🚀 Verify Page</span>
                )}
              </button>
            </form>

            {/* Error Message */}
            {error && (
              <div className="mt-6 bg-red-50 border border-red-200 rounded-lg p-4">
                <div className="flex items-start">
                  <span className="text-red-600 text-2xl mr-3">⚠️</span>
                  <div>
                    <h3 className="text-red-800 font-semibold">Error</h3>
                    <p className="text-red-700 mt-1">{error}</p>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Results */}
          {result && (
            <div className="space-y-6">
              {/* Analysis */}
              <div className="bg-white rounded-lg shadow-xl p-8">
                <h2 className="text-2xl font-bold text-gray-900 mb-4 flex items-center">
                  <span className="mr-3">🤖</span>
                  AI Analysis
                </h2>
                <div className="prose max-w-none">
                  <div className="bg-gray-50 rounded-lg p-6 border border-gray-200">
                    <p className="text-gray-800 whitespace-pre-wrap">{result.analysis}</p>
                  </div>
                </div>
              </div>

              {/* Screenshot */}
              <div className="bg-white rounded-lg shadow-xl p-8">
                <h2 className="text-2xl font-bold text-gray-900 mb-4 flex items-center">
                  <span className="mr-3">📸</span>
                  Full-Page Screenshot
                </h2>
                <div className="border border-gray-200 rounded-lg overflow-hidden">
                  <img
                    src={result.screenshot}
                    alt="Page screenshot"
                    className="w-full h-auto"
                  />
                </div>
                <p className="text-sm text-gray-500 mt-4">
                  ℹ️ This screenshot includes all page content, including sections below the fold.
                  The page was automatically scrolled and collapsible content was expanded.
                </p>
              </div>
            </div>
          )}

          {/* Loading State with Progress */}
          {loading && (
            <div className="bg-white rounded-lg shadow-xl p-8">
              <div className="text-center mb-6">
                <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-4 border-indigo-600 mb-4"></div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">Processing...</h3>
              </div>
              
              {/* Progress Log */}
              {statusMessages.length > 0 && (
                <div className="bg-gray-900 rounded-lg p-4 max-h-96 overflow-y-auto font-mono text-sm">
                  {statusMessages.map((message, index) => (
                    <div 
                      key={index} 
                      className="text-green-400 mb-1 animate-fadeIn"
                    >
                      {message}
                    </div>
                  ))}
                  <div className="text-green-400 animate-pulse">▊</div>
                  <div ref={statusEndRef} />
                </div>
              )}
            </div>
          )}
        </div>
      </main>
    </>
  );
}
