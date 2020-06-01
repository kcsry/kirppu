import ResultTable from "./result_table.jsx";

export function item_find_table() {
    return (
        <ResultTable head={
            <tr>
                <th className="receipt_index">#</th>
                <th className="receipt_code">{gettext('code')}</th>
                <th className="receipt_item">{gettext('item')}</th>
                <th className="receipt_price">{gettext('price')}</th>
                <th className="receipt_type">{gettext('type')}</th>
                <th className="receipt_name">{gettext('vendor')}</th>
                <th className="receipt_status">{gettext('status')}</th>
            </tr>
        }/>
    )
}

export function item_find_table_item({item, index, onClick}) {
    const vendor = dPrintF("%n (%i)", {
        n: item.vendor.name,
        i: item.vendor.id
    })

    let name_field = item.name
    if (item.box != null) {
        const box_number = item.box.box_number != null ? item.box.box_number : "??"
        name_field = [
            <span>{name_field + " "}</span>,
            <span className="label label-info">{"#" + box_number + ", n=" + item.box.item_count}</span>
        ]
    }

    let price_field
    if (item.box != null && item.box.bundle_size > 1) {
        price_field = displayPrice(item.price) + " / " + item.box.bundle_size
    } else {
        price_field = displayPrice(item.price)
    }

    return (
        <tr className={"receipt_tr_clickable" + (item.hidden ? " text-muted" : "")}
            onclick={() => onClick(item)}>
            <td className="receipt_index numeric">{index}</td>
            <td className="receipt_code">{item.code}</td>
            <td className="receipt_item">{name_field}</td>
            <td className="receipt_price numeric">{price_field}</td>
            <td className="receipt_type">{item.itemtype_display}</td>
            <td className="receipt_name">{vendor}</td>
            <td className="receipt_status">{item.state_display}</td>
        </tr>
    )
}

export function item_find_table_no_results() {
    return (
        <tr>
            <td colSpan="2"/>
            <td colSpan="5">{gettext("No results.")}</td>
        </tr>
    )
}
