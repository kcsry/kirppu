// In purchase and vendor checkout modes.

export function item_receipt_table({caption, autoNumber, splitTitle}) {
    return (
        <table className={"table table-striped table-hover table-condensed" + (autoNumber ? " auto-number" : "")}>
            {caption && <caption className="h3">{caption}</caption>}
            <thead>
            <tr>
                <th className="receipt_index numeric">{gettext("#")}</th>
                <th className="receipt_code">{gettext("code")}</th>
                {splitTitle && <th className="receipt_item">{gettext("item")}</th>}
                {splitTitle && <th className="receipt_item_detail"/>}
                {!splitTitle && <th colSpan="2" className="receipt_item">{gettext("item")}</th>}
                <th className="receipt_price">{gettext("price")}</th>
            </tr>
            </thead>
            <tbody/>
        </table>

    )
}

export function item_receipt_table_row({index, code, name, details, price}) {
    return (
        <tr id={code}>
            <td className="receipt_index numeric row-number">{index}</td>
            <td className="receipt_code">{code}</td>
            {details && <td className="receipt_item">{name}</td>}
            {details && <td className="receipt_item_detail">{details}</td>}
            {!details && <td colSpan="2" className="receipt_item">{name}</td>}
            <td className="receipt_price numeric">{price}</td>
        </tr>
    )
}
