// In overseer receipt list receipt and in purchase continuing suspended receipt.

import {dateTime} from './helpers'

function notes(notes) {
    return [
        <h4>{gettext("Notes")}</h4>,
        <ul>
            {notes.map((note) =>
                <li>{dateTime(note.timestamp)} <em>{note.clerk.print}</em>: {note.text}</li>
            )}
        </ul>
    ]
}

function items(items) {
    return [
        <h4>{gettext("Items")}</h4>,
        <table className="table table-condensed table-striped">
            <tbody>
            {items.map((item, index) =>
            <tr>
                <td className="numeric">{item.action === "DEL" && "-"}{index + 1}</td>
                <td className="receipt_code">{item.box_number ? "#" + item.box_number : item.code}</td>
                <td>{item.name}</td>
                <td className="numeric">{item.action === "DEL" && "-"}{displayPrice(item.price)}</td>
            </tr>
            )}
            </tbody>
        </table>
    ]
}

export default function render({receipt}) {
    return (
        <div>
            <dl className="dl-horizontal">
                <dt>{gettext("began")}</dt>
                <dd>{dateTime(receipt.start_time)}</dd>

                <dt>{gettext("sum")}</dt>
                <dd>{displayPrice(receipt.total)}</dd>

                <dt>{gettext("status")}</dt>
                <dd>{receipt.status_display}</dd>

                <dt>{gettext("clerk")}</dt>
                <dd>{receipt.clerk.print}</dd>

                <dt>{gettext("counter")}</dt>
                <dd>{receipt.counter}</dd>
            </dl>
            {receipt.notes && receipt.notes.length && notes(receipt.notes) || ""}
            {receipt.items && receipt.items.length && items(receipt.items) || ""}
        </div>
    )
}
