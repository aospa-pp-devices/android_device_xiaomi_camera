#!/usr/bin/env -S PYTHONPATH=../../../tools/extract-utils python3
#
# SPDX-FileCopyrightText: 2024 The LineageOS Project
# SPDX-License-Identifier: Apache-2.0
#

from extract_utils.fixups_blob import (
    blob_fixup,
    blob_fixups_user_type,
)
from extract_utils.fixups_lib import (
    lib_fixups,
    lib_fixups_user_type,
)
from extract_utils.main import (
    ExtractUtils,
    ExtractUtilsModule,
)

namespace_imports = []

def lib_fixup_campostproc_system_suffix(lib: str, partition: str, *args, **kwargs):
    return f'{lib}_system' if partition == 'system' else None

lib_fixups: lib_fixups_user_type = {
    **lib_fixups,
    (
        'vendor.xiaomi.hardware.campostproc@1.0',
    ): lib_fixup_campostproc_system_suffix,
}

blob_fixups: blob_fixups_user_type = {
    'system/lib64/libgui-xiaomi.so': blob_fixup()
        .replace_needed(
            'android.hardware.graphics.common-V6-ndk.so',
            'android.hardware.graphics.common-V7-ndk.so',
        ),
    (
        'system/lib64/libcamera_algoup_jni.xiaomi.so',
        'system/lib64/libcamera_mianode_jni.xiaomi.so',
    ): blob_fixup()
        .replace_needed(
            'libgui.so',
            'libgui-xiaomi.so',
        ),
    'system/priv-app/MiuiCamera/MiuiCamera.apk': blob_fixup()
        .apktool_unpack('patches')
        .patch_dir('patches')
        .apktool_pack(),
}

module = ExtractUtilsModule(
    'camera',
    'xiaomi',
    blob_fixups=blob_fixups,
    lib_fixups=lib_fixups,
    namespace_imports=namespace_imports,
)

if __name__ == '__main__':
    utils = ExtractUtils.device(module)
    utils.run()
