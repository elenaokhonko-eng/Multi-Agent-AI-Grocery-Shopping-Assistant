import { useEffect, useState } from 'react';

export const ApiTestComponent = () => {
  const [testResult, setTestResult] = useState<string>('Testing...');

  useEffect(() => {
    const testApi = async () => {
      try {
        console.log('Testing API connection...');
        const response = await fetch('http://localhost:3001/api/health');
        console.log('Response status:', response.status);
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Response data:', data);
        setTestResult(`Success: ${data.message}`);
      } catch (error) {
        console.error('API test failed:', error);
        setTestResult(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`);
      }
    };

    testApi();
  }, []);

  return (
    <div style={{ 
      position: 'fixed', 
      top: '10px', 
      right: '10px', 
      background: 'white', 
      padding: '10px', 
      border: '1px solid #ccc',
      borderRadius: '5px',
      zIndex: 9999
    }}>
      <h4>API Test:</h4>
      <p>{testResult}</p>
    </div>
  );
};
