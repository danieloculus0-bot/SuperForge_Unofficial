(() => {
  const menu = document.getElementById("context-menu");
  function hide(){ menu.hidden = true; menu.innerHTML = ""; }
  async function show(x,y,target){
    const entityType = target?.dataset?.entityType || document.body.dataset.entityType || "global";
    const entityId = target?.dataset?.entityId || document.body.dataset.entityId || "";
    const params = new URLSearchParams({entity_type:entityType, entity_id:entityId});
    const response = await fetch("/api/context-menu?" + params.toString());
    const items = await response.json();
    menu.innerHTML = '<div class="ctx-title">Open with</div>' + items.map(item =>
      '<a href="' + item.url + '"><span>' + item.title + '</span><small>' + item.area + '</small></a>'
    ).join("");
    menu.style.left = Math.min(x, window.innerWidth - 330) + "px";
    menu.style.top = Math.min(y, window.innerHeight - 520) + "px";
    menu.hidden = false;
  }
  document.addEventListener("contextmenu", e => {
    e.preventDefault();
    const target = e.target.closest(".context-target") || e.target.closest("[data-entity-type]") || document.body;
    show(e.clientX,e.clientY,target).catch(() => {});
  });
  document.addEventListener("click", hide);
  window.addEventListener("blur", hide);
})();
