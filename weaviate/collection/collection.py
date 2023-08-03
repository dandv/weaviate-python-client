import uuid as uuid_package
from dataclasses import dataclass
from typing import Dict, Any, Optional, List, Union, Tuple

from weaviate.collection.classes import (
    CollectionConfig,
    MetadataReturn,
    MetadataGet,
    RefToObject,
    BatchReference,
    DataObject,
)
from weaviate.collection.collection_base import CollectionBase, CollectionObjectBase
from weaviate.collection.collection_classes import Errors
from weaviate.collection.grpc import (
    GrpcBase,
    HybridFusion,
    MetadataQuery,
    PROPERTIES,
    HybridOptions,
    ReturnValues,
    GetOptions,
    BM25Options,
    NearVectorOptions,
    NearObjectOptions,
)
from weaviate.connect import Connection
from weaviate.data.replication import ConsistencyLevel
from weaviate.weaviate_types import UUIDS, UUID, BEACON


@dataclass
class _Object:
    data: Dict[str, Any]
    metadata: MetadataReturn


class _Grpc(GrpcBase):
    def get_flat(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        after: Optional[UUID] = None,
        return_metadata: Optional[MetadataQuery] = None,
        return_properties: Optional[PROPERTIES] = None,
    ) -> List[_Object]:
        return [
            self.__dict_to_obj(obj)
            for obj in self._get(limit, offset, after, return_metadata, return_properties)
        ]

    def get_options(self, returns: ReturnValues, options: Optional[GetOptions]) -> List[_Object]:
        if options is None:
            options = GetOptions()

        return [
            self.__dict_to_obj(obj)
            for obj in self._get(
                options.limit, options.offset, options.after, returns.metadata, returns.properties
            )
        ]

    def hybrid_flat(
        self,
        query: str,
        alpha: Optional[float] = None,
        vector: Optional[List[float]] = None,
        properties: Optional[List[str]] = None,
        fusion_type: Optional[HybridFusion] = None,
        limit: Optional[int] = None,
        autocut: Optional[int] = None,
        return_metadata: Optional[MetadataQuery] = None,
        return_properties: Optional[PROPERTIES] = None,
    ) -> List[_Object]:
        objects = self._hybrid(
            query,
            alpha,
            vector,
            properties,
            fusion_type,
            limit,
            autocut,
            return_metadata,
            return_properties,
        )
        return [self.__dict_to_obj(obj) for obj in objects]

    def hybrid_options(
        self,
        query: str,
        returns: ReturnValues,
        options: Optional[HybridOptions] = None,
    ) -> List[_Object]:
        if options is None:
            options = HybridOptions()

        objects = self._hybrid(
            query,
            options.alpha,
            options.vector,
            options.properties,
            options.fusion_type,
            options.limit,
            options.autocut,
            returns.metadata,
            returns.properties,
        )
        return [self.__dict_to_obj(obj) for obj in objects]

    def bm25_flat(
        self,
        query: str,
        properties: Optional[List[str]] = None,
        limit: Optional[int] = None,
        autocut: Optional[int] = None,
        return_metadata: Optional[MetadataQuery] = None,
        return_properties: Optional[PROPERTIES] = None,
    ) -> List[_Object]:
        return [
            self.__dict_to_obj(obj)
            for obj in self._bm25(
                query, properties, limit, autocut, return_metadata, return_properties
            )
        ]

    def bm25_options(
        self,
        query: str,
        returns: ReturnValues,
        options: Optional[BM25Options] = None,
    ) -> List[_Object]:
        if options is None:
            options = BM25Options()

        return [
            self.__dict_to_obj(obj)
            for obj in self._bm25(
                query,
                options.properties,
                options.limit,
                options.autocut,
                returns.metadata,
                returns.properties,
            )
        ]

    def near_vector_flat(
        self,
        vector: List[float],
        certainty: Optional[float] = None,
        distance: Optional[float] = None,
        autocut: Optional[int] = None,
        return_metadata: Optional[MetadataQuery] = None,
        return_properties: Optional[PROPERTIES] = None,
    ) -> List[_Object]:
        return [
            self.__dict_to_obj(obj)
            for obj in self._near_vector(
                vector, certainty, distance, autocut, return_metadata, return_properties
            )
        ]

    def near_vector_options(
        self,
        vector: List[float],
        returns: ReturnValues,
        options: Optional[NearVectorOptions] = None,
    ) -> List[_Object]:
        if options is None:
            options = NearVectorOptions()

        return [
            self.__dict_to_obj(obj)
            for obj in self._near_vector(
                vector,
                options.certainty,
                options.distance,
                options.autocut,
                returns.metadata,
                returns.properties,
            )
        ]

    def near_object_flat(
        self,
        obj: UUID,
        certainty: Optional[float] = None,
        distance: Optional[float] = None,
        autocut: Optional[int] = None,
        return_metadata: Optional[MetadataQuery] = None,
        return_properties: Optional[PROPERTIES] = None,
    ) -> List[_Object]:
        return [
            self.__dict_to_obj(obj)
            for obj in self._near_object(
                obj, certainty, distance, autocut, return_metadata, return_properties
            )
        ]

    def near_object_options(
        self,
        obj: UUID,
        returns: ReturnValues,
        options: Optional[NearObjectOptions] = None,
    ) -> List[_Object]:
        if options is None:
            options = NearObjectOptions()
        return [
            self.__dict_to_obj(obj)
            for obj in self._near_object(
                obj,
                options.certainty,
                options.distance,
                options.autocut,
                returns.metadata,
                returns.properties,
            )
        ]

    def __dict_to_obj(self, obj: Tuple[Dict[str, Any], MetadataReturn]) -> _Object:
        data: Dict[str, Any] = obj[0]
        for key in data.keys():
            if isinstance(data[key], List):
                for i, _ in enumerate(data[key]):
                    data[key][i] = self.__dict_to_obj(data[key][i])

        return _Object(data=data, metadata=obj[1])


class _Data:
    __collection: "CollectionObject"

    def __init__(self, collection: "CollectionObject") -> None:
        self.__collection = collection

    def insert(
        self,
        data: Dict[str, Any],
        uuid: Optional[UUID] = None,
        vector: Optional[List[float]] = None,
    ) -> uuid_package.UUID:
        weaviate_obj: Dict[str, Any] = {
            "class": self.__collection._name,
            "properties": {
                key: val if not isinstance(val, RefToObject) else val.to_beacon()
                for key, val in data.items()
            },
            "id": str(uuid if uuid is not None else uuid_package.uuid4()),
        }

        if vector is not None:
            weaviate_obj["vector"] = vector

        return self.__collection._insert(weaviate_obj)

    def insert_many(self, objects: List[DataObject]) -> List[Union[uuid_package.UUID, Errors]]:
        weaviate_objs: List[Dict[str, Any]] = [
            {
                "class": self.__collection._name,
                "properties": {
                    key: val if not isinstance(val, RefToObject) else val.to_beacon()
                    for key, val in obj.data.items()
                },
                "id": str(obj.uuid) if obj.uuid is not None else str(uuid_package.uuid4()),
            }
            for obj in objects
        ]

        return self.__collection._insert_many(weaviate_objs)

    def replace(
        self, data: Dict[str, Any], uuid: UUID, vector: Optional[List[float]] = None
    ) -> None:
        weaviate_obj: Dict[str, Any] = {
            "class": self.__collection._name,
            "properties": {
                key: val if not isinstance(val, RefToObject) else val.to_beacon()
                for key, val in data.items()
            },
        }
        if vector is not None:
            weaviate_obj["vector"] = vector

        self.__collection._replace(weaviate_obj, uuid=uuid)

    def update(
        self, data: Dict[str, Any], uuid: UUID, vector: Optional[List[float]] = None
    ) -> None:
        weaviate_obj: Dict[str, Any] = {
            "class": self.__collection._name,
            "properties": {
                key: val if not isinstance(val, RefToObject) else val.to_beacon()
                for key, val in data.items()
            },
        }
        if vector is not None:
            weaviate_obj["vector"] = vector

        self.__collection._update(weaviate_obj, uuid=uuid)

    def get_by_id(self, uuid: UUID, metadata: Optional[MetadataGet] = None) -> Optional[_Object]:
        ret = self.__collection._get_by_id(uuid=uuid, metadata=metadata)
        if ret is None:
            return ret
        return self.__collection._json_to_object(ret)

    def get(self, metadata: Optional[MetadataGet] = None) -> List[_Object]:
        ret = self.__collection._get(metadata=metadata)
        if ret is None:
            return []

        return [self.__collection._json_to_object(obj) for obj in ret["objects"]]

    def reference_add(self, from_uuid: UUID, from_property: str, to_uuids: UUIDS) -> None:
        self.__collection._reference_add(
            from_uuid=from_uuid, from_property_name=from_property, to_uuids=to_uuids
        )

    def reference_batch_add(self, from_property: str, refs: List[BatchReference]) -> None:
        refs_dict = [
            {
                "from": BEACON + f"{self._name}/{ref.from_uuid}/{from_property}",
                "to": BEACON + str(ref.to_uuid),
            }
            for ref in refs
        ]
        self.__collection._reference_batch_add(refs_dict)

    def reference_delete(self, from_uuid: UUID, from_property: str, to_uuids: UUIDS) -> None:
        self.__collection._reference_delete(
            from_uuid=from_uuid, from_property_name=from_property, to_uuids=to_uuids
        )

    def reference_replace(self, from_uuid: UUID, from_property: str, to_uuids: UUIDS) -> None:
        self.__collection._reference_replace(
            from_uuid=from_uuid, from_property_name=from_property, to_uuids=to_uuids
        )


class CollectionObject(CollectionObjectBase):
    def __init__(self, connection: Connection, name: str) -> None:
        super().__init__(connection, name)
        self.data = _Data(self)
        self.query = _Grpc(connection, name)

    def with_tenant(self, tenant: Optional[str] = None) -> "CollectionObject":
        return self._with_tenant(tenant)

    def with_consistency_level(
        self, consistency_level: Optional[ConsistencyLevel] = None
    ) -> "CollectionObject":
        return self._with_consistency_level(consistency_level)

    def _json_to_object(self, obj: Dict[str, Any]) -> _Object:
        return _Object(
            data={prop: val for prop, val in obj["properties"].items()},
            metadata=MetadataReturn(**obj),
        )


class Collection(CollectionBase):
    def create(self, config: CollectionConfig) -> CollectionObject:
        name = super()._create(config)
        if config.name != name:
            raise ValueError(
                f"Name of created collection ({name}) does not match given name ({config.name})"
            )
        return CollectionObject(self._connection, config.name)

    def get(self, name: str) -> CollectionObject:
        return CollectionObject(self._connection, name)

    def delete(self, name: str) -> None:
        self._delete(name)

    def exists(self, name: str) -> bool:
        return self._exists(name)
