import { NextRequest, NextResponse } from 'next/server'
import { v4 as uuidv4 } from 'uuid'

const LANGFLOW_URL = process.env.LANGFLOW_URL || 'http://localhost:7860'
const LANGFLOW_FLOW_ID = process.env.LANGFLOW_FLOW_ID || '346acaa3-2e85-4478-8ed1-16929cdfde0a'
const LANGFLOW_API_KEY = process.env.LANGFLOW_API_KEY || ''

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { message, session_id } = body
    
    if (!message) {
      return NextResponse.json(
        { error: 'Message is required' },
        { status: 400 }
      )
    }

    // Call Langflow API
    const langflowPayload = {
      output_type: 'chat',
      input_type: 'chat',
      input_value: message,
      session_id: session_id || uuidv4(),
    }

    // Build headers - include API key if provided
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    }
    // Note: Langflow v1.5+ requires authentication
    // Either set LANGFLOW_API_KEY or run Langflow with LANGFLOW_SKIP_AUTH_AUTO_LOGIN=true
    if (LANGFLOW_API_KEY) {
      headers['x-api-key'] = LANGFLOW_API_KEY
    }

    const langflowResponse = await fetch(
      `${LANGFLOW_URL}/api/v1/run/${LANGFLOW_FLOW_ID}`,
      {
        method: 'POST',
        headers,
        body: JSON.stringify(langflowPayload),
      }
    )

    // Get response as text first to check for HTML errors
    const responseText = await langflowResponse.text()
    
    // Check if response is HTML (error page)
    if (responseText.trim().startsWith('<!DOCTYPE') || responseText.trim().startsWith('<html')) {
      console.error('Langflow returned HTML:', responseText.substring(0, 200))
      return NextResponse.json(
        { error: 'Langflow returned an error page. Check if the flow ID is correct and Langflow is configured properly.' },
        { status: 502 }
      )
    }

    if (!langflowResponse.ok) {
      console.error('Langflow error:', responseText)
      
      // Try to parse error message
      try {
        const errorData = JSON.parse(responseText)
        const errorMsg = errorData.detail || errorData.message || errorData.error || 'Unknown error'
        return NextResponse.json(
          { error: `Langflow error: ${errorMsg}` },
          { status: langflowResponse.status }
        )
      } catch {
        return NextResponse.json(
          { error: `Langflow API error: ${langflowResponse.status}` },
          { status: langflowResponse.status }
        )
      }
    }

    // Parse JSON response
    let langflowData
    try {
      langflowData = JSON.parse(responseText)
    } catch (e) {
      console.error('Failed to parse Langflow response:', responseText.substring(0, 500))
      return NextResponse.json(
        { error: 'Invalid JSON response from Langflow' },
        { status: 502 }
      )
    }
    // Extract answer from Langflow response
    // The response structure may vary - handle common patterns
    let answer = ''
    
    if (langflowData.outputs) {
      // Handle array of outputs
      for (const output of langflowData.outputs) {
        if (output.outputs) {
          for (const innerOutput of output.outputs) {
            if (innerOutput.results?.message?.text) {
              answer = innerOutput.results.message.text
            } else if (innerOutput.results?.text) {
              answer = innerOutput.results.text
            } else if (innerOutput.message?.text) {
              answer = innerOutput.message.text
            }
          }
        }
      }
    } else if (langflowData.result) {
      answer = typeof langflowData.result === 'string' 
        ? langflowData.result 
        : langflowData.result.text || JSON.stringify(langflowData.result)
    } else if (langflowData.text) {
      answer = langflowData.text
    }

    if (!answer) {
      answer = 'No response received from the RAG system.'
    }

    // Return response
    return NextResponse.json({
      answer,
      session_id: session_id || langflowPayload.session_id,
    })

  } catch (error) {
    console.error('Chat API error:', error)
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Internal server error' },
      { status: 500 }
    )
  }
}

