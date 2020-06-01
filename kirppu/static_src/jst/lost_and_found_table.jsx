import ResultTable from "./result_table.jsx";

export function lost_and_found_table() {
    return (
        <ResultTable head={
            <tr>
                <th className="receipt_code">{gettext("code")}</th>
                <th className="receipt_item">{gettext("item")}</th>
                <th className="receipt_item_state">{gettext("state")}</th>
                <th className="receipt_vendor_id">{gettext("vendor")}</th>
            </tr>
        }/>
    )
}

export function lost_and_found_table_item({item}) {
    return (
        <tr>
            <td>{item.code}</td>
            <td>{item.name}</td>
            <td>{item.state_display}</td>
            <td>{item.vendor}</td>
        </tr>
    )
}
