/* Trazo page logic. No framework, no external requests except the API.
   The photo is resized here before upload. The server never stores it. */
(function () {
  "use strict";

  /* Upload constants. Longest side 1600 px, JPEG quality 0.8. Starting guess. */
  var MAX_SIDE = 1600;
  var JPEG_QUALITY = 0.8;
  var REQUEST_TIMEOUT_MS = 120000;

  var screens = {
    home: document.getElementById("screen-home"),
    loading: document.getElementById("screen-loading"),
    result: document.getElementById("screen-result"),
    error: document.getElementById("screen-error")
  };

  var loadingThumb = document.getElementById("loading-thumb");
  var resultBanner = document.getElementById("result-banner");
  var resultThumb = document.getElementById("result-thumb");
  var resultThumbBtn = document.getElementById("result-thumb-btn");
  var resultRows = document.getElementById("result-rows");
  var notesWrap = document.getElementById("result-notes-wrap");
  var resultNotes = document.getElementById("result-notes");
  var errorMessage = document.getElementById("error-message");

  var objectUrl = null;

  ["input-camera", "input-gallery", "input-again-camera", "input-again-gallery",
   "input-retry-camera", "input-retry-gallery"].forEach(function (id) {
    var input = document.getElementById(id);
    if (input) input.addEventListener("change", function () { handleFile(input.files[0]); });
  });

  resultThumbBtn.addEventListener("click", function () {
    var expanded = resultThumbBtn.getAttribute("aria-expanded") === "true";
    resultThumbBtn.setAttribute("aria-expanded", String(!expanded));
    resultThumbBtn.setAttribute("aria-label", expanded ? "Enlarge prescription photo" : "Shrink prescription photo");
  });

  function show(name) {
    Object.keys(screens).forEach(function (key) {
      screens[key].hidden = key !== name;
    });
    document.getElementById("main").scrollIntoView();
  }

  function escapeHtml(value) {
    return String(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function unreadable() {
    return '<span class="unread">Could not read</span>';
  }

  function fieldLine(label, value) {
    if (value === null || value === undefined || value === "") {
      return '<p class="med-meta"><span class="label">' + escapeHtml(label) + ":</span> " + unreadable() + "</p>";
    }
    return '<p class="med-meta"><span class="label">' + escapeHtml(label) + ":</span> " + escapeHtml(value) + "</p>";
  }

  function handleFile(file) {
    if (!file) return;
    setObjectUrl(file);
    show("loading");
    resizeImage(file, MAX_SIDE, JPEG_QUALITY).then(function (jpeg) {
      return postPhoto(jpeg);
    }).then(function (payload) {
      renderResult(payload);
    }).catch(function (err) {
      renderError(err);
    });
  }

  function setObjectUrl(file) {
    if (objectUrl) URL.revokeObjectURL(objectUrl);
    objectUrl = URL.createObjectURL(file);
    loadingThumb.src = objectUrl;
    resultThumb.src = objectUrl;
    resultThumbBtn.setAttribute("aria-expanded", "false");
    resultThumbBtn.setAttribute("aria-label", "Enlarge prescription photo");
  }

  function resizeImage(file, maxSide, quality) {
    return new Promise(function (resolve, reject) {
      var url = URL.createObjectURL(file);
      var img = new Image();
      img.onload = function () {
        URL.revokeObjectURL(url);
        var scale = Math.min(1, maxSide / Math.max(img.width, img.height));
        var canvas = document.createElement("canvas");
        canvas.width = Math.max(1, Math.round(img.width * scale));
        canvas.height = Math.max(1, Math.round(img.height * scale));
        canvas.getContext("2d").drawImage(img, 0, 0, canvas.width, canvas.height);
        canvas.toBlob(function (blob) {
          if (blob) resolve(blob);
          else reject(new Error("The photo could not be prepared. Try again."));
        }, "image/jpeg", quality);
      };
      img.onerror = function () {
        URL.revokeObjectURL(url);
        reject(new Error("That file is not an image."));
      };
      img.src = url;
    });
  }

  function postPhoto(blob) {
    var controller = new AbortController();
    var timer = setTimeout(function () { controller.abort(); }, REQUEST_TIMEOUT_MS);
    var form = new FormData();
    form.append("image", blob, "prescription.jpg");
    return fetch("/read", { method: "POST", body: form, signal: controller.signal })
      .then(function (response) {
        clearTimeout(timer);
        return response.json().then(function (body) {
          if (!response.ok) {
            var err = new Error(body.error || "The photo could not be read. Check the connection and try again.");
            err.retake = body.retake === true;
            throw err;
          }
          return body;
        });
      })
      .catch(function (err) {
        clearTimeout(timer);
        if (err.name === "AbortError") {
          throw new Error("The reading service did not answer within 2 minutes. Try again with a clearer photo.");
        }
        if (err instanceof Error) throw err;
        throw new Error("The reading service could not be reached. Check the connection and try again.");
      });
  }

  function renderResult(payload) {
    resultBanner.textContent = payload.banner || "";
    resultRows.innerHTML = "";
    var rows = payload.medicines || [];
    if (rows.length === 0) {
      resultRows.innerHTML = '<li class="empty-note">No medicines were found on this page. Try a clearer photo.</li>';
    }
    rows.forEach(function (row, index) {
      resultRows.appendChild(buildRow(row, index));
    });
    if (payload.notes) {
      resultNotes.textContent = payload.notes;
      notesWrap.hidden = false;
    } else {
      notesWrap.hidden = true;
    }
    show("result");
    requestAnimationFrame(function () {
      var items = resultRows.querySelectorAll(".med.enter");
      items.forEach(function (item, i) {
        setTimeout(function () { item.classList.remove("enter"); }, 40 * i);
      });
    });
  }

  function stampClass(status) {
    if (status === "OK") return "stamp-ok";
    if (status === "Check this") return "stamp-check";
    return "stamp-unclear";
  }

  function buildRow(row, index) {
    var li = document.createElement("li");
    li.className = "med enter";

    var html = "";
    if (row.name) {
      html += '<h2 class="med-name">' + escapeHtml(row.name) + "</h2>";
    } else {
      html += '<h2 class="med-name">' + unreadable() + "</h2>";
    }
    html += '<span class="stamp ' + stampClass(row.status) + '">' + escapeHtml(row.status || "Unclear") + "</span>";

    var timing = row.timing_known ? row.timing_text : row.timing_code;
    html += metaLine("Strength", row.strength);
    html += metaLine("Take", timing);
    html += metaLine("Days", row.duration);

    if (row.status !== "OK" && row.reason) {
      html += '<p class="reason">' + escapeHtml(row.reason) + "</p>";
    }
    (row.candidates || []).forEach(function (c) {
      var label = [c.brand_name, c.generic_name].filter(Boolean).join(" / ");
      if (c.strength) label += ", " + c.strength;
      html += '<p class="candidate">Possible match: ' + escapeHtml(label) + " (" + escapeHtml(String(c.score)) + ")</p>";
    });
    if (row.suggestion) {
      html += '<p class="suggestion">A saved correction suggests ' + escapeHtml(row.suggestion) + ". Confirm it before relying on it.</p>";
    }

    /* Corrections need the model's reading as raw text. Rows with no
       readable name have nothing to attach a correction to. */
    if (row.name) {
      html += '<button type="button" class="correct-toggle" data-row="' + index + '">Correct name</button>';
      html += '<div class="editor" hidden>' +
        "<label>Model reading<input type=\"text\" readonly value=\"" + escapeHtml(row.name) + "\"></label>" +
        "<label>Correction<input type=\"text\" maxlength=\"200\" autocomplete=\"off\" placeholder=\"Type the correct name\"></label>" +
        '<p class="save-note" hidden></p>' +
        '<div class="editor-row">' +
        '<button type="button" class="btn btn-primary" data-save>Save correction</button>' +
        '<button type="button" class="btn" data-cancel>Cancel</button>' +
        "</div></div>";
    }

    li.innerHTML = html;

    var toggle = li.querySelector(".correct-toggle");
    if (toggle) {
      var editor = li.querySelector(".editor");
      toggle.addEventListener("click", function () {
        editor.hidden = !editor.hidden;
        toggle.textContent = editor.hidden ? "Correct name" : "Hide editor";
      });
      li.querySelector("[data-cancel]").addEventListener("click", function () {
        editor.hidden = true;
        toggle.textContent = "Correct name";
      });
      li.querySelector("[data-save]").addEventListener("click", function () {
        saveCorrection(row.name, li);
      });
    }
    return li;
  }

  function metaLine(label, value) {
    return fieldLine(label, value === undefined ? null : value);
  }

  function saveCorrection(rawText, li) {
    var input = li.querySelector(".editor input:not([readonly])");
    var note = li.querySelector(".save-note");
    var corrected = input.value.trim();
    note.hidden = false;
    if (!corrected) {
      note.textContent = "Type the correct name before saving.";
      return;
    }
    note.textContent = "Saving.";
    fetch("/correct", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ raw_text: rawText, corrected_name: corrected })
    }).then(function (response) {
      return response.json().then(function (body) {
        if (!response.ok) throw new Error(body.error || "The correction could not be saved.");
        note.textContent = body.verified
          ? "Saved. It matches the medicine list and will be suggested with a Check this flag."
          : "Saved. It will be suggested with a Check this flag once it matches the medicine list.";
      });
    }).catch(function (err) {
      note.textContent = err.message || "The correction could not be saved.";
    });
  }

  function renderError(err) {
    errorMessage.textContent = err.message || "The photo could not be read. Check the connection and try again.";
    show("error");
  }
})();
