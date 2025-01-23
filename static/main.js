const fetchDataBtn = document.getElementById("fetchDataBtn");
const platformSelect = document.getElementById("platformSelect");
const displayNameInput = document.getElementById("displayNameInput");

const godSelectionSection = document.getElementById("godSelectionSection");
const godListSelect = document.getElementById("godListSelect");

const godSortSelect = document.getElementById("godSortSelect");

const resultsSection = document.getElementById("resultsSection");
const godNameHeading = document.getElementById("godNameHeading");
const buildSummariesDiv = document.getElementById("buildSummaries");
const itemFrequencyList = document.getElementById("itemFrequencyList");

let buildsSummary = {};       // Summarized builds from the server
let itemDataMap = {};         // We'll load items.json for tooltips

const loadingSpinner = document.getElementById("loadingSpinner");
const statusMessage = document.getElementById("statusMessage");

async function loadItems() {
  try {
    // We'll fetch items.json from the same Flask server 
    // because we have an endpoint for it (/items.json).
    const resp = await fetch("/items.json");
    if (!resp.ok) {
      console.warn("Could not fetch /items.json, proceeding with empty item data");
      return;
    }
    const itemsArray = await resp.json();
    itemsArray.forEach(itemObj => {
      if (itemObj.Item_Id) {
        itemDataMap[itemObj.Item_Id] = itemObj;
      }
      if (itemObj.DisplayName) {
        itemDataMap[itemObj.DisplayName] = itemObj;
      }
    });
  } catch (err) {
    console.error("Error loading items.json:", err);
  }
}

// Populate the God dropdown
function populateGodDropdown(summaryData, sortMode = "alpha") {
  godListSelect.innerHTML = "";

  // summaryData is something like:
  // {
  //   "Agni": [ { "build": [...], "count": 2 }, { ... } ],
  //   "Apollo": [ { ... } ],
  //   ...
  // }

  // Compute usage for each god by summing up the counts of all builds
  let usageArray = [];
  for (const godName of Object.keys(summaryData)) {
    let totalMatches = 0;
    const buildsForGod = summaryData[godName];
    // buildsForGod is an array of { build: [...], count: <number> }
    for (const buildInfo of buildsForGod) {
      totalMatches += buildInfo.count;
    }
    usageArray.push({ god: godName, usage: totalMatches });
  }

  // Sort usageArray based on the selected sort mode
  if (sortMode === "usage") {
    // Sort by usage descending, then alpha if tie
    usageArray.sort((a, b) => {
      const diff = b.usage - a.usage;
      if (diff !== 0) return diff;
      return a.god.localeCompare(b.god);
    });
  } else {
    // Alphabetical by default
    usageArray.sort((a, b) => a.god.localeCompare(b.god));
  }

  // Now populate the select with "GodName (X matches)"
  usageArray.forEach(entry => {
    const option = document.createElement("option");
    option.value = entry.god; // e.g. "Agni"
    // for the label, e.g. "Agni (3 matches)"
    option.textContent = `${entry.god} (${entry.usage} matches)`;
    godListSelect.appendChild(option);
  });

  if (usageArray.length === 0) {
    godSelectionSection.style.display = "none";
    return;
  }
  godSelectionSection.style.display = "block";
}

// Event handler for changing the sort type
godSortSelect.addEventListener("change", () => {
  const newSortMode = godSortSelect.value; // "alpha" or "usage"
  // Re-populate the dropdown with the new sort mode
  populateGodDropdown(buildsSummary, newSortMode);
});

// Show info for a selected god
function showGodDetails(godName) {
  resultsSection.style.display = "block";
  godNameHeading.textContent = `Builds for ${godName}`;

  const buildsArr = buildsSummary[godName] || [];
  buildSummariesDiv.innerHTML = "";
  itemFrequencyList.innerHTML = "";

  // 1) Render each known build
  buildsArr.forEach((buildInfo, idx) => {
    const { build, count } = buildInfo;
    const card = document.createElement("div");
    card.classList.add("build-card");
    card.innerHTML = `<h4>Build #${idx + 1} (used ${count} times)</h4>
                      <div class="item-list"></div>`;
    const itemListDiv = card.querySelector(".item-list");

    build.forEach(itemName => {
      // Look up the object in itemDataMap by name or ID
      const itemObj = itemDataMap[itemName];
      itemListDiv.appendChild(createItemElement(itemObj));
    });

    buildSummariesDiv.appendChild(card);
  });

  // 2) Summarize item usage across all builds for that god
  const itemUsageMap = {};
  buildsArr.forEach(buildInfo => {
    buildInfo.build.forEach(itemName => {
      itemUsageMap[itemName] = (itemUsageMap[itemName] || 0) + buildInfo.count;
    });
  });

  // Sort descending by usage
  const usageArray = Object.entries(itemUsageMap)
      .map(([k, v]) => ({ itemName: k, usage: v }))
      .sort((a, b) => b.usage - a.usage);

  usageArray.forEach(entry => {
    const li = document.createElement("li");
    // Convert the name to an object for tooltip rendering
    const itemObj = itemDataMap[entry.itemName];
    const itemElem = createItemElement(itemObj);

    li.appendChild(itemElem);
    li.appendChild(document.createTextNode(` - chosen ${entry.usage} times`));
    itemFrequencyList.appendChild(li);
  });
}

// Helper: create an item element with tooltip
function createItemElement(itemObj) {
  // DEBUG: Check what itemObj we receive
  console.log("[DEBUG] createItemElement called with itemObj:", itemObj);

  const span = document.createElement("span");
  span.classList.add("item");
  span.textContent = itemObj?.DisplayName || "Unknown Item";

  // DEBUG: If itemObj is falsy, we can't proceed
  if (!itemObj) {
    console.error("[DEBUG] itemObj is falsy. Possibly a mismatch with item ID or name.");
  } else {
    // If itemObj has an Item_Id, see if itemsById is returning anything
    console.log("[DEBUG] itemObj.Item_Id:", itemObj.Item_Id,
      " => itemsById[itemObj.Item_Id]:", itemsById[itemObj.Item_Id]);
  }

  if (itemObj) {
    const tooltip = document.createElement("div");
    tooltip.classList.add("tooltip");
    const title = itemObj.DisplayName || "Item";
    const desc = itemObj.Description || "(No description)";
    tooltip.innerHTML = `<strong>${title}</strong><br/>${desc}`;
    span.appendChild(tooltip);
  }

  return span;
}

function showLoadingState(msg) {
  statusMessage.textContent = msg;
  loadingSpinner.style.display = "flex"; 
  fetchDataBtn.disabled = true;
}

function hideLoadingState() {
  loadingSpinner.style.display = "none";
  statusMessage.textContent = "";
  fetchDataBtn.disabled = false;
}

// Event listeners
fetchDataBtn.addEventListener("click", async () => {
  const platformVal = platformSelect.value;
  const displayVal = displayNameInput.value.trim();
  if (!platformVal || !displayVal) {
    alert("Please enter a valid platform and display name!");
    return;
  }

  showLoadingState(`Fetching builds for ${displayVal} on ${platformVal}...`);
  // 1) Load items first, so our itemDataMap is populated
  await loadItems();

  // 2) Fetch build summary from the server with the chosen platform/display name
  try {
    // 3) Populate the God dropdown
    populateGodDropdown(buildsSummary, "alpha");
    resultsSection.style.display = "none";
  } catch (err) {
    alert(`Error fetching data: ${err}`);
  } finally {
    hideLoadingState();
  }
});

// Event listener for selecting a god from the dropdown
godListSelect.addEventListener("change", () => {
  const selectedGod = godListSelect.value;
  if (selectedGod) {
    showGodDetails(selectedGod);
  }
});

// Wait for DOM to load
document.addEventListener("DOMContentLoaded", () => {
  const fetchDataBtn = document.getElementById("fetchDataBtn");
  if (fetchDataBtn) {
    fetchDataBtn.addEventListener("click", handleFetchData);
  }
});

async function handleFetchData() {
  const platform = document.getElementById("platformSelect").value.trim();
  const displayName = document.getElementById("displayNameInput").value.trim();
  const maxMatches = parseInt(document.getElementById("maxMatchesInput").value, 10) || 10;

  // Ensure within 1 to 300
  const safeMaxMatches = Math.min(Math.max(maxMatches, 1), 300);

  // Access loading UI elements
  const loadingSpinner = document.getElementById("loadingSpinner");
  const statusMessage = document.getElementById("statusMessage");
  const fetchDataBtn = document.getElementById("fetchDataBtn");

  if (!platform || !displayName) {
    alert("Please enter both platform and display name!");
    return;
  }

  // Provide user feedback while fetching
  fetchDataBtn.disabled = true;
  fetchDataBtn.textContent = "Fetching...";
  loadingSpinner.style.display = "inline-block";
  statusMessage.textContent = `Fetching up to ${safeMaxMatches} matches for ${displayName} on ${platform}...`;

  try {
    const url = `/api/s2_fetch_full_data?platform=${encodeURIComponent(platform)}`
              + `&display_name=${encodeURIComponent(displayName)}`
              + `&max_matches=${safeMaxMatches}`;
    const response = await fetch(url);
    const data = await response.json();

    if (response.ok) {
      // Render the data to the page
      renderFullPlayerData(data);
      statusMessage.textContent = `Success! Showing data for ${displayName}.`;
    } else {
      throw new Error(data.error || "Unknown error occurred.");
    }
  } catch (err) {
    statusMessage.textContent = `Error: ${err.message}`;
  } finally {
    // Restore button & hide spinner
    fetchDataBtn.disabled = false;
    fetchDataBtn.textContent = "Fetch Full Data";
    loadingSpinner.style.display = "none";
  }
}

// Renders the full player data returned by S2_fetch_full_player_data_by_displayname
function renderFullPlayerData(data) {
  // Sections
  const playerInfoSection = document.getElementById("playerInfoSection");
  const playerStatsSection = document.getElementById("playerStatsSection");
  const matchHistorySection = document.getElementById("matchHistorySection");
  const buildSummarySection = document.getElementById("buildSummarySection");

  // Make these sections visible
  playerInfoSection.style.display = "block";
  playerStatsSection.style.display = "block";
  matchHistorySection.style.display = "block";
  buildSummarySection.style.display = "block";

  // 1) Render Player Info
  renderPlayerInfo(data.PlayerInfo);

  // 2) Render Player Stats
  renderPlayerStats(data.PlayerStats);

  // 3) Render Match History
  renderMatchHistory(data.MatchHistory);

  // 4) Summarize builds
  renderBuildSummary(data.MatchHistory);
}

function renderPlayerInfo(playerInfo) {
  const container = document.getElementById("playerInfoContainer");
  container.innerHTML = "";

  if (!playerInfo || !playerInfo.display_names) {
    container.textContent = "No player info available.";
    return;
  }

  const ul = document.createElement("ul");
  playerInfo.display_names.forEach(displayNameObj => {
    for (const nameKey in displayNameObj) {
      const playerArray = displayNameObj[nameKey];
      playerArray.forEach(p => {
        const li = document.createElement("li");
        li.textContent = `DisplayName: ${nameKey}, PlayerID: ${p.player_id}, PlayerUUID: ${p.player_uuid}`;
        // Show linked portals
        if (p.linked_portals && p.linked_portals.length > 0) {
          const portalInfo = p.linked_portals
            .map(lp => `${lp.platform}: ${lp.display_name}`)
            .join("; ");
          li.textContent += ` (Linked: ${portalInfo})`;
        }
        ul.appendChild(li);
      });
    }
  });
  container.appendChild(ul);
}

function renderPlayerStats(playerStats) {
  const container = document.getElementById("playerStatsContainer");
  container.innerHTML = "";

  if (!Array.isArray(playerStats) || playerStats.length === 0) {
    container.textContent = "No stats to show.";
    return;
  }

  playerStats.forEach(ps => {
    const div = document.createElement("div");
    div.classList.add("stats-box");
    div.innerHTML = `<strong>Player UUID:</strong> ${ps.player_uuid} <br/>`;

    // For example, might have ps.stats = { total_matches_played: 735 }
    for (const [key, val] of Object.entries(ps.stats)) {
      div.innerHTML += `<strong>${key}:</strong> ${val} <br/>`;
    }
    container.appendChild(div);
  });
}

function renderMatchHistory(matchHistory) {
  const container = document.getElementById("matchHistoryContainer");
  container.innerHTML = "";

  // (1) Filter out unknown gods
  const filteredMatches = matchHistory.filter(m => m.god_name !== "UnknownGod");

  if (!Array.isArray(filteredMatches) || filteredMatches.length === 0) {
    container.textContent = "No match history found (or all were UnknownGod).";
    return;
  }

  const table = document.createElement("table");
  table.classList.add("pro-table");
  table.innerHTML = `
    <thead>
      <tr>
        <th>Match ID</th>
        <th>God</th>
        <th>Role</th>
        <th>Kills</th>
        <th>Deaths</th>
        <th>Assists</th>
        <th>Items</th>
      </tr>
    </thead>
    <tbody></tbody>
  `;
  const tbody = table.querySelector("tbody");

  filteredMatches.forEach(m => {
    const row = document.createElement("tr");
    const kills = m.basic_stats?.Kills || 0;
    const deaths = m.basic_stats?.Deaths || 0;
    const assists = m.basic_stats?.Assists || 0;

    // Gather items as full objects instead of just DisplayNames
    const itemList = [];
    if (m.items) {
      for (const slotKey of Object.keys(m.items)) {
        const itemObj = m.items[slotKey];
        // Store the entire object
        itemList.push(itemObj);
      }
    }

    row.innerHTML = `
      <td>${m.match_id}</td>
      <td>${m.god_name || "UnknownGod"}</td>
      <td>${m.played_role ?? m.assigned_role ?? "N/A"}</td>
      <td>${kills}</td>
      <td>${deaths}</td>
      <td>${assists}</td>
      <td id="itemsCell"></td>
    `;
    tbody.appendChild(row);

    const itemsCell = row.querySelector("#itemsCell");
    
    // Pass the entire item object to createItemElement
    itemList.forEach(itemObj => {
      const itemEl = createItemElement(itemObj);
      itemsCell.appendChild(itemEl);
    });
  });

  container.appendChild(table);
}

function renderBuildSummary(matchHistory) {
  const container = document.getElementById("buildSummaryContainer");
  container.innerHTML = "";

  const filteredMatches = (Array.isArray(matchHistory)
    ? matchHistory.filter(m => m.god_name !== "UnknownGod")
    : []);

  if (!filteredMatches.length) {
    container.textContent = "No matches to summarize (or all were UnknownGod).";
    return;
  }

  const buildsByGod = {};

  filteredMatches.forEach(match => {
    const godName = match.god_name || "UnknownGod";
    const sortedSlots = match.items ? Object.keys(match.items).sort() : [];
    // Collect full item objects
    const buildArray = sortedSlots.map(slot => match.items[slot]);

    // For display only, we build a string of item DisplayNames:
    const buildKey = buildArray
      .map(item => item?.DisplayName || "UnknownItem")
      .join(" + ");

    if (!buildsByGod[godName]) {
      buildsByGod[godName] = {};
    }

    // Instead of just a numeric count, store an object with count & items
    if (!buildsByGod[godName][buildKey]) {
      buildsByGod[godName][buildKey] = {
        count: 0,
        items: buildArray
      };
    }

    buildsByGod[godName][buildKey].count++;
  });

  const summaryDiv = document.createElement("div");
  for (const god in buildsByGod) {
    const godDiv = document.createElement("div");
    godDiv.innerHTML = `<h3>${god}</h3>`;
    const ul = document.createElement("ul");

    // Now each buildStr entry is an object with count & items
    for (const buildStr in buildsByGod[god]) {
      const { count, items } = buildsByGod[god][buildStr];
      const li = document.createElement("li");

      // Create a span or similar container for each item's tooltip
      if (Array.isArray(items)) {
        items.forEach((itemObj, idx) => {
          // Use your createItemElement for tooltips
          const itemSpan = createItemElement(itemObj);
          li.appendChild(itemSpan);

          // If you want a separator between item icons
          if (idx < items.length - 1) {
            li.appendChild(document.createTextNode(" + "));
          }
        });
      }

      // After listing items, show how many times that build was used
      li.appendChild(
        document.createTextNode(` - used ${count} time(s)`)
      );
      ul.appendChild(li);
    }

    godDiv.appendChild(ul);
    summaryDiv.appendChild(godDiv);
  }
  container.appendChild(summaryDiv);
}

// -------------------------------------------------------------------
// (3) Improve the item tooltip to show description + stats
// If you already have a createItemElement() or similar, update it:
// -------------------------------------------------------------------
function createItemElement(itemObj) {
  // This function receives an item object with keys like:
  // {
  //   "DisplayName": "Bumba's Cudgel",
  //   "Description": "...",
  //   "Stats": [ { "TagName": "...", "Value": ... }, ... ]
  //   ...
  // }

  const span = document.createElement("span");
  span.classList.add("item");
  span.textContent = itemObj?.DisplayName || "Unknown Item";

  if (itemObj) {
    const tooltip = document.createElement("div");
    tooltip.classList.add("tooltip");

    const title = itemObj.DisplayName || "Item";
    const desc = itemObj.Description || "(No description)";
    const stats = itemObj.Stats || [];

    // Convert stats to a bullet list
    // e.g. TagName="Character.Stat.MaxHealth", Value=50 => "+50 MaxHealth"
    let statsHtml = "";
    if (stats.length > 0) {
      statsHtml = "<ul class='item-stats'>";
      stats.forEach(stat => {
        // For a more MOBA-like short label, remove "Character.Stat." prefix:
        const shortName = stat.TagName.replace(/^Character\.Stat\./, "");
        statsHtml += `<li>+${stat.Value} ${shortName}</li>`;
      });
      statsHtml += "</ul>";
    }

    tooltip.innerHTML = `
      <strong class="item-title">${title}</strong>
      <div class="item-desc">${desc}</div>
      ${statsHtml}
    `;

    span.appendChild(tooltip);
  }

  return span;
}

function getItemTooltipHtml(itemData) {
  // DEBUG: See what itemData we get
  console.log("[DEBUG] getItemTooltipHtml -> itemData:", itemData);

  if (!itemData) {
    return "Unknown Item";
  }
  
  // UPDATED: Use the 'Item_Id' directly
  const itemId = itemData.Item_Id; 
  const itemInfo = itemsById[itemId]; // <-- itemsById should match "Item_Id" keys
  
  // DEBUG: Show the ID and what we find in itemsById
  console.log("[DEBUG] Mapped itemId:", itemId, " => itemInfo:", itemInfo);

  if (!itemInfo) {
    return "Unknown Item";
  }
  
  // Return a tooltip or display string from the item's properties.
  let tooltipHtml = `<strong>${itemInfo.DisplayName}</strong>`;
  if (itemInfo.Description) {
    tooltipHtml += `<br>${itemInfo.Description}`;
  }
  return tooltipHtml;
} 