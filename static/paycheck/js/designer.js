(() => {
    const overlay = document.getElementById("overlay");
    const fieldList = document.getElementById("field-list");
    const fieldsInput = document.getElementById("fields-json");
    const existingRaw = document.getElementById("existing-fields");

    if (!overlay || !fieldList || !fieldsInput || !existingRaw) {
        return;
    }

    const parseFields = () => {
        try {
            const parsed = JSON.parse(existingRaw.textContent || "[]");
            if (Array.isArray(parsed)) {
                return parsed;
            }
            if (parsed && typeof parsed === "object") {
                return Object.values(parsed);
            }
            return [];
        } catch (err) {
            return [];
        }
    };

    let fields = parseFields();
    if (!Array.isArray(fields)) {
        fields = [];
    }
    let drawing = false;
    let startX = 0;
    let startY = 0;
    let tempBox = null;
    let interaction = null;

    const clamp = (value, min, max) => Math.min(Math.max(value, min), max);
    const escapeHtml = (text) => String(text)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/\"/g, "&quot;")
        .replace(/'/g, "&#39;");

    const toPercent = (x, y, w, h) => {
        const rect = overlay.getBoundingClientRect();
        return {
            x: clamp((x / rect.width) * 100, 0, 100),
            y: clamp((y / rect.height) * 100, 0, 100),
            w: clamp((w / rect.width) * 100, 0.1, 100),
            h: clamp((h / rect.height) * 100, 0.1, 100),
        };
    };

    const ensureUniqueKeys = () => {
        const seen = new Set();
        fields.forEach((field, index) => {
            const base = String(field.key || "").trim().replace(/\s+/g, "_") || `field_${index + 1}`;
            let key = base;
            let suffix = 2;
            while (seen.has(key)) {
                key = `${base}_${suffix}`;
                suffix += 1;
            }
            field.key = key;
            seen.add(key);
        });
    };

    const sync = () => {
        ensureUniqueKeys();
        fieldsInput.value = JSON.stringify(fields);
    };

    const repaint = () => {
        ensureUniqueKeys();
        overlay.querySelectorAll(".field-box").forEach((node) => node.remove());
        fieldList.innerHTML = "";

        fields.forEach((field, index) => {
            const box = document.createElement("div");
            box.className = "field-box";
            box.style.left = `${field.x}%`;
            box.style.top = `${field.y}%`;
            box.style.width = `${field.w}%`;
            box.style.height = `${field.h}%`;
            box.title = `${field.label} (${field.key})`;
            box.textContent = field.label;

            const handle = document.createElement("span");
            handle.className = "field-resize-handle";
            handle.title = "Resize";
            box.appendChild(handle);

            box.addEventListener("mousedown", (event) => {
                if (event.target === handle) {
                    return;
                }
                event.preventDefault();
                event.stopPropagation();
                interaction = {
                    type: "drag",
                    index,
                    startClientX: event.clientX,
                    startClientY: event.clientY,
                    startX: field.x,
                    startY: field.y,
                    startW: field.w,
                    startH: field.h,
                    box,
                };
            });

            handle.addEventListener("mousedown", (event) => {
                event.preventDefault();
                event.stopPropagation();
                interaction = {
                    type: "resize",
                    index,
                    startClientX: event.clientX,
                    startClientY: event.clientY,
                    startX: field.x,
                    startY: field.y,
                    startW: field.w,
                    startH: field.h,
                    box,
                };
            });

            box.addEventListener("dblclick", (ev) => {
                ev.stopPropagation();
                fields.splice(index, 1);
                repaint();
            });

            overlay.appendChild(box);

            const li = document.createElement("li");
            li.className = "field-item";
            li.innerHTML = `
                <label>Key</label>
                <input type="text" class="field-input field-key" value="${escapeHtml(field.key || "")}">
                <label>Label</label>
                <input type="text" class="field-input field-label" value="${escapeHtml(field.label || "")}">
                <label>Font (mm)</label>
                <input type="number" step="0.1" min="1.5" max="12" class="field-input field-font" value="${Number(field.font_size_mm || 3.5)}">
                <div class="field-meta">${field.x.toFixed(1)}%, ${field.y.toFixed(1)}% | ${field.w.toFixed(1)}% x ${field.h.toFixed(1)}%</div>
            `;

            const keyInput = li.querySelector(".field-key");
            const labelInput = li.querySelector(".field-label");
            const fontInput = li.querySelector(".field-font");

            keyInput.addEventListener("input", (event) => {
                const raw = String(event.target.value || "").trim().replace(/\s+/g, "_");
                fields[index].key = raw || `field_${index + 1}`;
                sync();
            });

            labelInput.addEventListener("input", (event) => {
                const raw = String(event.target.value || "").trim();
                fields[index].label = raw || fields[index].key;
                box.textContent = fields[index].label;
                box.title = `${fields[index].label} (${fields[index].key})`;
                sync();
            });

            fontInput.addEventListener("input", (event) => {
                const parsed = Number.parseFloat(String(event.target.value || "3.5"));
                fields[index].font_size_mm = Number.isFinite(parsed) ? clamp(parsed, 1.5, 12) : 3.5;
                sync();
            });

            fieldList.appendChild(li);
        });

        sync();
    };

    const nextFieldKey = () => {
        if (!Array.isArray(fields)) {
            fields = [];
        }
        const used = new Set(fields.map((f) => String(f.key || "")));
        let counter = fields.length + 1;
        while (used.has(`field_${counter}`)) {
            counter += 1;
        }
        return `field_${counter}`;
    };

    const finalizeDraw = (clientX, clientY) => {
        if (!drawing || !tempBox) {
            return;
        }

        drawing = false;
        const rect = overlay.getBoundingClientRect();
        const endX = clamp(clientX - rect.left, 0, rect.width);
        const endY = clamp(clientY - rect.top, 0, rect.height);

        const left = Math.min(startX, endX);
        const top = Math.min(startY, endY);
        const width = Math.abs(endX - startX);
        const height = Math.abs(endY - startY);

        tempBox.remove();
        tempBox = null;

        if (width < 8 || height < 8) {
            return;
        }

        const key = nextFieldKey();
        const label = `Field ${fields.length + 1}`;
        const normalized = toPercent(left, top, width, height);

        fields.push({
            key,
            label,
            ...normalized,
            font_size_mm: 3.5,
        });

        repaint();
    };

    const updateInteraction = (clientX, clientY) => {
        if (!interaction) {
            return;
        }

        const rect = overlay.getBoundingClientRect();
        const deltaXPercent = ((clientX - interaction.startClientX) / rect.width) * 100;
        const deltaYPercent = ((clientY - interaction.startClientY) / rect.height) * 100;
        const field = fields[interaction.index];
        if (!field) {
            interaction = null;
            return;
        }

        if (interaction.type === "drag") {
            field.x = clamp(interaction.startX + deltaXPercent, 0, 100 - field.w);
            field.y = clamp(interaction.startY + deltaYPercent, 0, 100 - field.h);
        } else {
            field.w = clamp(interaction.startW + deltaXPercent, 0.1, 100 - field.x);
            field.h = clamp(interaction.startH + deltaYPercent, 0.1, 100 - field.y);
        }

        interaction.box.style.left = `${field.x}%`;
        interaction.box.style.top = `${field.y}%`;
        interaction.box.style.width = `${field.w}%`;
        interaction.box.style.height = `${field.h}%`;
        sync();
    };

    overlay.addEventListener("mousedown", (event) => {
        if (event.target !== overlay) {
            return;
        }
        if (interaction) {
            return;
        }
        drawing = true;
        const rect = overlay.getBoundingClientRect();
        startX = event.clientX - rect.left;
        startY = event.clientY - rect.top;

        tempBox = document.createElement("div");
        tempBox.className = "field-box";
        tempBox.style.left = `${startX}px`;
        tempBox.style.top = `${startY}px`;
        tempBox.style.width = "0px";
        tempBox.style.height = "0px";
        overlay.appendChild(tempBox);
    });

    overlay.addEventListener("mousemove", (event) => {
        if (interaction) {
            updateInteraction(event.clientX, event.clientY);
            return;
        }
        if (!drawing || !tempBox) {
            return;
        }
        const rect = overlay.getBoundingClientRect();
        const currentX = clamp(event.clientX - rect.left, 0, rect.width);
        const currentY = clamp(event.clientY - rect.top, 0, rect.height);

        const left = Math.min(startX, currentX);
        const top = Math.min(startY, currentY);
        const width = Math.abs(currentX - startX);
        const height = Math.abs(currentY - startY);

        tempBox.style.left = `${left}px`;
        tempBox.style.top = `${top}px`;
        tempBox.style.width = `${width}px`;
        tempBox.style.height = `${height}px`;
    });

    overlay.addEventListener("mouseup", (event) => {
        if (interaction) {
            interaction = null;
            repaint();
            return;
        }
        finalizeDraw(event.clientX, event.clientY);
    });

    window.addEventListener("mouseup", (event) => {
        if (interaction) {
            interaction = null;
            repaint();
            return;
        }
        finalizeDraw(event.clientX, event.clientY);
    });

    window.addEventListener("mousemove", (event) => {
        if (interaction) {
            updateInteraction(event.clientX, event.clientY);
        }
    });

    overlay.addEventListener("mouseleave", () => {
        if (drawing && tempBox) {
            tempBox.remove();
            tempBox = null;
            drawing = false;
        }
    });

    const designerForm = document.getElementById("designer-form");
    if (designerForm) {
        designerForm.addEventListener("submit", () => {
            sync();
        });
    }

    repaint();
})();
