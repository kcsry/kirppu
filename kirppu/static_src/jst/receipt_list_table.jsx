import {dateTime} from './helpers'

// In vendor report, compensations list.
export function receipt_list_table_compensations({items, caption}) {
    return (
        <table className="table table-striped table-hover table-condensed">
            {caption && <caption className="h3">{caption}</caption>}
            <thead>
            <tr>
                <th className="numeric">{gettext("#")}</th>
                <th>{gettext("compensated at")}</th>
                <th className="numeric">{gettext("sum")}</th>
                <th>{gettext("clerk (counter)")}</th>
            </tr>
            </thead>
            <tbody>
            {items.map((item, index) =>
                <tr data-index={index} data-id={item.id}>
                    <td className="numeric">{index + 1}</td>
                    <td>{dateTime(item.start_time)}</td>
                    <td className="numeric">{displayPrice(item.total)}</td>
                    <td>{item.clerk.print} ({item.counter})</td>
                </tr>
            )}
            </tbody>
        </table>
    )
}

// In login if multiple receipts exist.
export function receipt_list_table_simple({items, caption}) {
    return (
        <table className="table table-striped table-hover table-condensed">
            {caption && <caption className="h3">{caption}</caption>}
            <thead>
            <tr>
                <th className="numeric">{gettext("#")}</th>
                <th>{gettext("began")}</th>
                <th className="numeric">{gettext("sum")}</th>
                <th>{gettext("counter")}</th>
            </tr>
            </thead>
            <tbody>
            {items.map((item, index) =>
                <tr data-index={index}>
                    <td className="numeric">{index}</td>
                    <td>{dateTime(item.start_time)}</td>
                    <td className="numeric">{displayPrice(item.total)}</td>
                    <td>{item.counter}</td>
                </tr>
            )}
            </tbody>
        </table>
    )
}
