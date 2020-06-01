
export function receipt_table({caption, vendor, code, item, price}) {
    return (
        <table className="table table-striped table-hover table-condensed">
            {caption && <caption className="h3">{caption}</caption>}
            <thead>
            <tr>
                <th className="receipt_vendor_id">{vendor}</th>
                <th className="receipt_code">{code}</th>
                <th className="receipt_item">{item}</th>
                <th className="receipt_price">{price}</th>
            </tr>
            </thead>
            <tbody/>
        </table>
    )
}

export function receipt_table_row({joined, vendor, code, name, price, text}) {
    if (joined) {
        return <td colSpan="4">{text}</td>
    }
    return (
        <tr id={code}>
            <td className="receipt_vendor_id numeric">{vendor}</td>
            <td className="receipt_code">{code}</td>
            <td className="receipt_item">{name}</td>
            <td className="receipt_price numeric">{price}</td>
        </tr>
    )
}
