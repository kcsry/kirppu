function THTwist({value, extraClasses}) {
    return (
        <th className={"thin-table-head " + (extraClasses ?? "")}>
            <div><span>{value}</span></div>
        </th>
    )
}

function ViewBtnCell() {
    return <td><button type="button" className={"btn btn-sm btn-default row-edit"}>{gettext("Edit")}</button></td>
}


function editBtns() {
    return [
        <button type="button" data-action="cancel" className={"btn btn-sm row-edit btn-warning"}>{gettext("Cancel")}</button>,
        <button type="button" data-action="save" className={"btn btn-sm row-edit btn-primary"}>{gettext("Save")}</button>
    ]
}

function EditBtnCell() {
    return <td>{editBtns()}</td>
}

function THEditBtnCell() {
    return <th>{editBtns()}</th>
}

function TextCell({value}) {
    return <td>{value}</td>
}

function THText({value}) {
    return <th>{value}</th>
}

function BoolEditCell({value, name}) {
    return <td><input type="checkbox" name={name} checked={value}/></td>
}

function BoolViewCell({value}) {
    return <td><span className={"glyphicon " + (value
        ? "glyphicon-ok-sign text-success"
        : "glyphicon-remove-sign text-danger")}> </span></td>
}

/**
 * @param value {String} String to hyphenate.
 * @param chunk {number} Length of chunk.
 * @return {String} Soft-hyphenated string.
 */
function hyphenateChunk(value, chunk) {
    let output = "";
    let start = 0;
    for (let i = chunk; i < value.length; i += chunk) {
        output += value.slice(start, i)
        output += "\u00ad";
        start = i;
    }
    output += value.slice(start);
    return output;
}

function CodeViewCell({value, realValue}) {
    if (value) {
        return <td>{hyphenateChunk(realValue, 7)}</td>
    }
    return BoolViewCell({value})
}

function CodeEditCell({value, realValue, name, availableClerks}) {
    return (
        <td>
            <select name={name}>
                <option value="remove">{gettext("Remove code")}</option>
                <option value="generate">{gettext("Generate new code")}</option>
                <optgroup label={gettext("Keep current value")}>
                    <option selected value="keep">{(realValue === null || realValue === "") ? gettext("[none]") : realValue}</option>
                </optgroup>
                <optgroup label={gettext("Change code")}>
                    {availableClerks.map((val) => {
                        return <option value={"c_" + val}>{val}</option>
                    })}
                </optgroup>
            </select>
        </td>
    )
}


function rowContent({info, edit, th, availableClerks}) {
    if (edit && th) {
        throw Error("Illegal argument combination")
    }

    let Btn = ViewBtnCell;
    let BoolCell = BoolViewCell;
    let CodeCell = CodeViewCell;
    let Text = TextCell;

    if (edit) {
        Btn = EditBtnCell;
        BoolCell = BoolEditCell;
        CodeCell = CodeEditCell;
    } else if (th) {
        Btn = THEditBtnCell;
        BoolCell = THTwist;
        CodeCell = THTwist;
        Text = THText;
    }
    return [
        <Btn value={""} className="button-cell"/>,
        <Text value={info.name}/>,
        <BoolCell value={info.is_clerk} name={"is_clerk"}/>,
        <CodeCell value={info.has_clerk_code} realValue={info.clerk_code} name={"has_clerk_code"} extraClasses="thin-table-head-separate" availableClerks={availableClerks}/>,
        <BoolCell value={info.manage_event} name={"manage_event"}/>,
        <BoolCell value={info.see_clerk_codes} name={"see_clerk_codes"}/>,
        <BoolCell value={info.see_statistics} name={"see_statistics"}/>,
        <BoolCell value={info.see_accounting} name={"see_accounting"}/>,
        <BoolCell value={info.register_items_outside_registration} name={"register_items_outside_registration"}/>,
        <BoolCell value={info.perform_overseer_actions} name={"perform_overseer_actions"}/>,
        <BoolCell value={info.switch_sub_vendor} name={"switch_sub_vendor"}/>,
        <BoolCell value={info.create_sub_vendor} name={"create_sub_vendor"}/>,
    ]
}

export function PersonRow({info, index, edit, availableClerks}) {
    return (
        <tr id={"row_" + info.id} data-id={info.id} data-index={index} data-editing={edit ?? false}>
            {rowContent({info: info, edit: edit, availableClerks: availableClerks})}
        </tr>
    )
}

function TableHead() {
    const info = {
        name: gettext("Name"),
        is_clerk: gettext("Is a clerk"),
        has_clerk_code: gettext("Has access code"),
        manage_event: gettext("Manage event"),
        see_clerk_codes: gettext("See clerk codes"),
        see_statistics: gettext("See statistics"),
        see_accounting: gettext("See accounting"),
        register_items_outside_registration: gettext("Register items outside registration"),
        perform_overseer_actions: gettext("Perform overseer actions"),
        switch_sub_vendor: gettext("Switch sub vendor"),
        create_sub_vendor: gettext("Create sub vendor"),
    }
    return (
        <thead>
        <tr>
            {rowContent({info: info, th: true})}
        </tr>
        </thead>
    )
}

export function person_info_table(infos, edit) {
    return (
        <table className="table table-striped twisted-heading">
            <TableHead/>
            <tbody>
            {infos.map((item, index) => {
                return <PersonRow info={item} index={index} edit={edit}/>
            })}
            </tbody>
        </table>
    )
}
