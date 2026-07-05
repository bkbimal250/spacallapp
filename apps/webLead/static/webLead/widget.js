(function () {
  function currentScript() {
    return document.currentScript || document.querySelector('script[data-key][src*="widget.js"]');
  }

  function apiBase(script) {
    try {
      return new URL(script.src).origin;
    } catch (error) {
      return window.location.origin;
    }
  }

  function cssValue(value, fallback) {
    return value || fallback;
  }

  function renderError(container, message) {
    var error = container.querySelector(".mc-weblead-error");
    if (error) error.textContent = message || "";
  }

  function init(script) {
    if (!script || script.dataset.mcLoaded === "true") return;
    script.dataset.mcLoaded = "true";

    var formKey = script.getAttribute("data-key");
    if (!formKey) return;

    var mount = document.getElementById("mastercall-form");
    if (!mount) {
      mount = document.createElement("div");
      script.parentNode.insertBefore(mount, script);
    }

    var base = apiBase(script);
    fetch(base + "/api/v1/web-leads/config/" + encodeURIComponent(formKey) + "/")
      .then(function (response) {
        if (!response.ok) throw new Error("Unable to load form.");
        return response.json();
      })
      .then(function (config) {
        var primary = cssValue(script.getAttribute("data-primary-color"), config.primary_color);
        var button = cssValue(script.getAttribute("data-button-color"), config.button_color);
        var background = cssValue(script.getAttribute("data-background-color"), config.background_color);
        var text = cssValue(script.getAttribute("data-text-color"), config.text_color);
        var radius = cssValue(script.getAttribute("data-radius"), config.border_radius);
        var width = cssValue(script.getAttribute("data-width"), "420px");
        var font = cssValue(script.getAttribute("data-font-family"), config.font_family);

        mount.innerHTML =
          '<form class="mc-weblead-form">' +
          '<h3 class="mc-weblead-title"></h3>' +
          '<input name="name" type="text" required placeholder="Name" autocomplete="name">' +
          '<input name="phone" type="tel" required placeholder="Phone" autocomplete="tel">' +
          '<input name="address" type="text" required maxlength="20" placeholder="Address">' +
          '<input name="notes" type="text" maxlength="20" placeholder="Notes">' +
          '<button type="submit"></button>' +
          '<div class="mc-weblead-error" aria-live="polite"></div>' +
          '<div class="mc-weblead-success" aria-live="polite"></div>' +
          "</form>";

        var form = mount.querySelector("form");
        var title = mount.querySelector(".mc-weblead-title");
        var submit = mount.querySelector("button");
        var success = mount.querySelector(".mc-weblead-success");

        title.textContent = config.form_title || "Book Appointment";
        submit.textContent = config.submit_button_text || "Submit";
        form.style.cssText =
          "box-sizing:border-box;width:100%;max-width:" + width + ";padding:18px;border:1px solid " + primary +
          ";border-radius:" + radius + ";background:" + background + ";color:" + text +
          ";font-family:" + font + ",Arial,sans-serif;display:grid;gap:12px;";
        title.style.cssText = "margin:0 0 4px;font-size:20px;line-height:1.25;color:" + text + ";";
        Array.prototype.forEach.call(form.querySelectorAll("input"), function (input) {
          input.style.cssText =
            "box-sizing:border-box;width:100%;padding:11px 12px;border:1px solid #d7d7d7;border-radius:8px;font:inherit;color:" +
            text + ";background:#fff;";
        });
        submit.style.cssText =
          "width:100%;padding:12px 14px;border:0;border-radius:8px;background:" + button +
          ";color:#fff;font:inherit;font-weight:700;cursor:pointer;";
        mount.querySelector(".mc-weblead-error").style.cssText = "min-height:18px;color:#c62828;font-size:13px;";
        success.style.cssText = "min-height:18px;color:#167a3a;font-size:13px;";

        form.addEventListener("submit", function (event) {
          event.preventDefault();
          renderError(mount, "");
          success.textContent = "";
          submit.disabled = true;
          submit.textContent = "Submitting...";

          var payload = {
            form_key: formKey,
            name: form.name.value,
            phone: form.phone.value,
            address: form.address.value,
            notes: form.notes.value,
            submitted_from_url: window.location.href
          };

          fetch(base + "/api/v1/web-leads/submit/", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
          })
            .then(function (response) {
              return response.json().then(function (data) {
                if (!response.ok) throw data;
                return data;
              });
            })
            .then(function (data) {
              success.textContent = data.message || config.success_message;
              form.reset();
            })
            .catch(function (error) {
              var message = error.message || error.detail || "Please check the form and try again.";
              if (error.form_key) message = error.form_key;
              renderError(mount, Array.isArray(message) ? message[0] : message);
            })
            .finally(function () {
              submit.disabled = false;
              submit.textContent = config.submit_button_text || "Submit";
            });
        });
      })
      .catch(function (error) {
        mount.textContent = error.message || "Unable to load form.";
      });
  }

  init(currentScript());
  Array.prototype.forEach.call(document.querySelectorAll('script[data-key][src*="widget.js"]'), init);
})();
