import type { RequestHandler } from "@sveltejs/kit";
import { json } from "@sveltejs/kit";

export const POST: RequestHandler = async ({ request }) => {
  try {
    const search = await request.text();

    if (!search) {
      return new Response("No search term provided", { status: 400 });
    }
    const response = await fetch('http://127.0.0.1:5000/get-modules?module=' + encodeURIComponent(search), {
      method: 'GET',
    });
    if (!response.ok) {
      return new Response('Backend error', { status: 500 });
    }

    const data = await response.json();
    
    return json(data);

  } catch (err) {
    return new Response('Server error', { status: 500 });
  }
};