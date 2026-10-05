import type { RequestHandler } from "@sveltejs/kit";
import { json } from "@sveltejs/kit";

export const GET: RequestHandler = async () => {
  try {
    
    const response = await fetch('http://127.0.0.1:5000/modules/get-module/filters', {
      method: 'GET',
    });
    if (!response.ok) {
      return new Response('Backend error: ' + await response.text()
      , { status: 500 });
    }

    const data = await response.json();
    
    return json(data);

  } catch (err) {
    return new Response('Server error', { status: 500 });
  }
};