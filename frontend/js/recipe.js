// recipe.js — recipe list and detail panel

import { api } from "./api.js";

let _recipes = [];
let _selectedRecipe = null;

export function getSelectedRecipe() { return _selectedRecipe; }

export async function loadRecipeList() {
  const list = document.getElementById("recipe-list");
  try {
    _recipes = await api.listRecipes();
    renderList();
  } catch (e) {
    list.innerHTML = `<p class="error-msg">Failed to load recipes: ${e.message}</p>`;
  }
}

export function addRecipeToList(recipe) {
  _recipes.unshift(recipe);
  renderList();
  selectRecipe(recipe.id);
}

function renderList() {
  const list = document.getElementById("recipe-list");
  if (!_recipes.length) {
    list.innerHTML = `<p class="empty-hint">No recipes yet. Add one below!</p>`;
    return;
  }
  list.innerHTML = _recipes.map(r => `
    <div class="recipe-item${_selectedRecipe?.id === r.id ? " active" : ""}" data-id="${r.id}">
      <div class="recipe-item-title">${esc(r.title)}</div>
      <div class="recipe-item-meta">${[r.cuisine, r.step_count ? r.step_count + " steps" : null].filter(Boolean).join(" · ")}</div>
    </div>
  `).join("");

  list.querySelectorAll(".recipe-item").forEach(el => {
    el.addEventListener("click", () => selectRecipe(el.dataset.id));
  });
}

export async function selectRecipe(id) {
  try {
    _selectedRecipe = await api.getRecipe(id);
    renderDetail(_selectedRecipe);
    renderList();  // re-render to update active state
    document.dispatchEvent(new CustomEvent("recipeSelected", { detail: _selectedRecipe }));
  } catch (e) {
    console.error("Failed to select recipe:", e);
  }
}

function renderDetail(recipe) {
  document.getElementById("recipe-detail-empty").classList.add("hidden");
  const content = document.getElementById("recipe-detail-content");
  content.classList.remove("hidden");

  document.getElementById("detail-title").textContent = recipe.title;

  const meta = document.getElementById("detail-meta");
  const metaItems = [
    recipe.servings && `🍽 ${recipe.servings}`,
    recipe.prep_time_minutes && `⏱ Prep ${recipe.prep_time_minutes}m`,
    recipe.cook_time_minutes && `🔥 Cook ${recipe.cook_time_minutes}m`,
    recipe.cuisine && `🌍 ${recipe.cuisine}`,
  ].filter(Boolean);
  meta.innerHTML = metaItems.map(m => `<span>${m}</span>`).join("");

  const ingList = document.getElementById("detail-ingredients");
  ingList.innerHTML = recipe.ingredients.map(ing => {
    const parts = [ing.quantity, ing.unit, ing.name, ing.notes].filter(Boolean);
    return `<li>${esc(parts.join(" "))}</li>`;
  }).join("");

  const stepList = document.getElementById("detail-steps");
  stepList.innerHTML = recipe.steps.map((s, i) => `
    <li data-step="${i}">${esc(s.instruction)}</li>
  `).join("");

  // Click on step in detail panel to jump chat to that step
  stepList.querySelectorAll("li").forEach(li => {
    li.addEventListener("click", () => {
      document.dispatchEvent(new CustomEvent("jumpToStep", { detail: parseInt(li.dataset.step) }));
    });
  });
}

export function highlightStep(index) {
  document.querySelectorAll("#detail-steps li").forEach((li, i) => {
    li.classList.toggle("current-step", i === index);
  });
}

function esc(s) {
  return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}
