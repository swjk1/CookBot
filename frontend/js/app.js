// app.js — main app orchestrator

import { loadRecipeList, getSelectedRecipe } from "./recipe.js";
import { startCookingSession } from "./chat.js";
import { api } from "./api.js";

function el(id) { return document.getElementById(id); }

async function init() {
  await loadRecipeList();

  // Start cooking when recipe is selected + button clicked
  el("btn-start-cooking")?.addEventListener("click", async () => {
    const recipe = getSelectedRecipe();
    if (!recipe) return;

    try {
      const session = await api.startSession(recipe.id);
      await startCookingSession(recipe, session.session_id);
    } catch (e) {
      console.error("Failed to start session:", e);
      alert(`Could not start session: ${e.message}`);
    }
  });

  // New recipe button scrolls/focuses the ingest panel
  el("btn-new-recipe")?.addEventListener("click", () => {
    el("ingest-panel")?.scrollIntoView({ behavior: "smooth" });
    el("ingest-text")?.focus();
  });

  // Auto-start session when a recipe is selected (optional UX flow)
  document.addEventListener("recipeSelected", async (e) => {
    const recipe = e.detail;
    // Show recipe detail — the user can then click "Start Cooking"
    // (no auto-start, user must explicitly begin)
  });
}

document.addEventListener("DOMContentLoaded", init);
