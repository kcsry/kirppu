const YES_NO_INDICES = {
    "true": 0,
    "false": 1,
    "null": 2,
    "undefined": 2
}

// yesno-helper like one found in django templates.
export function yesNo(bValue, choices) {
    if (typeof(choices) != "string") {
        choices = "yes,no"
    }
    choices = choices.split(",")
    if (2 < choices.length || choices.length > 3) {
        console.error("Choices must contain either two or three words separated by comma!")
        return null
    }

    let sValue = "" + bValue
    if (!(sValue in YES_NO_INDICES)) {
        console.warn("Value not found in lookup table: " + sValue)
        sValue = "undefined"
    }
    return choices[Math.min(YES_NO_INDICES[sValue], choices.length - 1)]
}

const titlePattern = /((?:^|\s)\w)/g
export function title(str) {
    return str.replace(titlePattern, (m) => m.toUpperCase())
}

export function dateTime(value) {
    return DateTimeFormatter.datetime(value)
}

const parser = new DOMParser();
const memoizedNodeLists = {};
export function html(text) {
    let nodes;
    if (text in memoizedNodeLists) {
        nodes = memoizedNodeLists[text];
    } else {
        const doc = parser.parseFromString(text, "text/html");
        if (doc.body) {
            nodes = doc.body.childNodes;
            memoizedNodeLists[text] = nodes;
        } else {
            return doc;
        }
    }
    // ReDOM doesn't expect the nodelist to shrink while iterating and mounting elements.
    // - Convert the nodelist to an array which doesn't change.
    // - Clone nodes to prevent memoized nodes disappearing from present DOM.
    return Array.from(nodes, (n) => n.cloneNode(true));
}
