(function() {
    let select_dom = null;
    let initial_selection = null;
    let may_submit = false;
    let new_dialog = null;
    let new_vendor_url = null;

    function select_handler() {
        if (initial_selection == null) {
            select_dom = $("#vendor-select");
            initial_selection = select_dom.find("[selected=selected]").val();
            select_dom.parents("form").on("submit", function() {
                console.log("try submit " + may_submit);
                return may_submit;
            });

            new_dialog = $("#new_vendor_dialog");
            const new_form = $("#new_vendor_dialog_form");
            new_form.on("submit", function() {
                submit_new_vendor(new_form);
                return false;
            });
            const submit = new_dialog.find("#new_vendor_dialog_submit");
            submit.on("click", function() {
                submit_new_vendor(new_form, submit);
            });
            new_form.find("input").on("change", function() {
                new_form.removeClass("has-error");
            })
        }
        const current_dom = select_dom.find(":selected");

        const value = current_dom.val();
        if (value === "new") {
            // Restore initial (so add can be redone if canceled and needed).
            select_dom.val(initial_selection);
            new_dialog.modal('show');
        } else if (value !== initial_selection) {
            console.log("Starting submit for " + value);
            may_submit = true;
            select_dom.parents("form").submit();
        }
    }

    function submit_new_vendor(form, submit) {
        let any = false;
        let data = {};
        form.find("input").each(function() {
            const self = $(this);
            if (self.val().replace(/ /, "") !== "") {
                data[self.attr("name")] = self.val();
                any = true;
            }
        });
        if (!any) {
            form.addClass("has-error");
        } else {
            form.removeClass("has-error");
            if (new_vendor_url != null) {
                submit.prop("disabled", "disabled");
                $.post({
                    url: new_vendor_url,
                    data: data,
                }).done(function(result) {
                    select_dom.append($("<option>").attr("value", result.id).text("..."));
                    select_dom.val(result.id);
                    select_dom.change();
                }).fail(function(jqXHR) {
                    submit.prop("disabled", false);
                    const response = jqXHR.responseJSON;
                    for (let key in response) {
                        if (!response.hasOwnProperty(key)) {
                            continue;
                        }
                        // Just concat all errors to one message.
                        const errors = response[key];
                        let cat = "";
                        for (let error of errors) {
                            cat += error.message;
                            cat += " ";
                        }

                        const input_block = form.find("#" + key);
                        input_block.next(".help-block").text(cat);
                        input_block.parent().addClass("has-error");
                    }
                });
            }
        }
    }

    window.changeVendor = select_handler;
    window.setNewVendorUrl = function(url) {
        if (new_vendor_url == null) {
            new_vendor_url = url;
        }
    };

})();
