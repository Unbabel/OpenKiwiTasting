#  OpenKiwi: Open-Source Machine Translation Quality Estimation
#  Copyright (C) 2020 Unbabel <openkiwi@unbabel.com>
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
from pathlib import Path
from typing import Any, Dict, Optional, Union

from omegaconf import OmegaConf
from pydantic import BaseModel, BaseSettings, Extra


class ModelFields(BaseModel):
    LP: str
    URL: str


class ModelsSettings(BaseSettings):
    models: Dict[str, ModelFields]

    def __init__(
        __pydantic_self__,
        config: Optional[Union[str, Path]] = Path(__file__).parent / '../models.yaml',
        **data: Any
    ) -> None:
        if config is not None:
            config_path = Path(config).expanduser()
            config_dict = OmegaConf.load(config_path.open())
            if config_dict:
                data_config = OmegaConf.merge(config_dict, OmegaConf.create(data))
                data = OmegaConf.to_container(data_config)
        super().__init__(**data)

    class Config:
        # Throws an error whenever an extra key is provided, effectively making parsing
        # strict
        extra = Extra.forbid
