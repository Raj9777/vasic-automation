"use client";
import { useState } from 'react';
import axios from 'axios';

export default function Home() {
  const [url, setUrl] = useState('');
  const [leads, setLeads] = useState([]); // Changed from emails to leads
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState('');

  const handleScrape = async () => {
    if (!url) return;
    setLoading(true);
    setStatus('Scanning website... this may take 10-20 seconds...');
    setLeads([]);

    try {
      // Connect to your Python Backend
      const response = await axios.post('https://vasic-backend.onrender.com/scrape', { url });
      
      // Update state with the new LEADS list
      setLeads(response.data.leads);
      
      if (response.data.leads.length > 0) {
        setStatus(`Success! Found ${response.data.leads.length} verified leads.`);
      } else {
        setStatus('No emails found on this page.');
      }
    } catch (error) {
      setStatus('Error: Could not scan this site. Make sure Backend is running!');
      console.error(error);
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white flex flex-col items-center justify-center p-4">
      <h1 className="text-4xl font-bold mb-2 text-blue-400">Vasic Automation</h1>
      <p className="mb-8 text-gray-400">AI Lead Verification Engine</p>

      <div className="w-full max-w-md bg-gray-800 p-6 rounded-lg shadow-lg">
        <label className="block text-sm font-bold mb-2">Target Website URL</label>
        <input
          type="text"
          className="w-full p-3 rounded bg-gray-700 border border-gray-600 focus:outline-none focus:border-blue-500 mb-4"
          placeholder="example.com"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
        />

        <button
          onClick={handleScrape}
          disabled={loading}
          className={`w-full p-3 rounded font-bold transition ${
            loading ? 'bg-gray-600 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-500'
          }`}
        >
          {loading ? 'Scanning Engine Running...' : 'Find Decision Makers'}
        </button>

        {status && <p className="mt-4 text-center text-sm text-yellow-400">{status}</p>}

        {leads.length > 0 && (
          <div className="mt-6">
            <h3 className="text-lg font-bold mb-2 text-green-400">Verified Leads Found:</h3>
            <div className="bg-gray-900 rounded border border-gray-700 overflow-hidden">
              {leads.map((lead, index) => (
                <div key={index} className="p-3 border-b border-gray-800 last:border-0 flex justify-between items-center">
                  <div className="flex flex-col">
                    <span className="font-mono text-sm text-white">{lead.email}</span>
                    <span className="text-xs text-gray-500">{lead.source}</span>
                  </div>
                  <span className={`text-xs px-2 py-1 rounded font-bold ${
                    lead.confidence.includes('HIGH') ? 'bg-green-900 text-green-300' : 
                    lead.confidence.includes('Team') ? 'bg-yellow-900 text-yellow-300' : 'bg-blue-900 text-blue-300'
                  }`}>
                    {lead.confidence}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
