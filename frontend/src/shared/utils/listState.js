export const updateItemInList = (list, updatedItem) => {
    if (!updatedItem?.id) return list;
    return list.map(item =>
        item.id === updatedItem.id ? { ...item, ...updatedItem } : item
    );
};

export const removeItemFromList = (list, id) =>
    list.filter(item => item.id !== id);

export const addItemToList = (list, item) => {
    if (!item?.id || list.some(existing => existing.id === item.id)) {
        return list;
    }
    return [item, ...list];
};

export const mergeExistingItemsById = (list, freshItems) => {
    const freshById = new Map((freshItems || []).map(item => [item.id, item]));
    return list.map(item =>
        freshById.has(item.id) ? { ...item, ...freshById.get(item.id) } : item
    );
};
