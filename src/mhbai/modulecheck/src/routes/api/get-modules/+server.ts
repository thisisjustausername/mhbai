import type { RequestHandler } from "@sveltejs/kit";
import { json } from "@sveltejs/kit";

export const POST: RequestHandler = async ({ request }) => {
  try {
    const search = await request.json();
    if (!search) {
      return new Response("No search term provided", { status: 400 });
    }
    const response = await fetch('http://127.0.0.1:5000/modules/get-modules', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(search)
    });
    if (!response.ok) {
      return new Response(await response.text(), { status: response.status });
      return new Response(response.status === 500 ? 'Failed to fetch result' : await response.text(), { status: response.status });
    }

    const data = await response.json();
    
    return json(data);

  } catch (err) {
    return new Response('Server error', { status: 500 });
  }
};